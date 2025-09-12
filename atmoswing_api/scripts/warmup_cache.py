# Warmup script that prebuilds JSON responses for heavy aggregation & meta endpoints.
# Scans regions and recent forecast dates, compares latest source netCDF mtime to
# prebuilt JSON mtime, regenerates JSON atomically when needed.

import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

from atmoswing_api.app.services import aggregations as agg_svc
from atmoswing_api.app.services import meta as meta_svc
from atmoswing_api.app.utils.utils import compute_cache_hash, make_cache_paths


def resolve_data_dir(data_dir: str) -> Path:
    base = Path(data_dir)
    if not base.is_absolute():
        repo_root = Path(__file__).resolve().parents[3]
        base = (repo_root / base).resolve()
    return base


def atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


def acquire_lock(lock_path: Path, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False


def release_lock(lock_path: Path):
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def parse_forecast_date_from_filename(fname: str) -> str | None:
    # Expected name: YYYY-MM-DD_HH....nc
    base = os.path.basename(fname)
    parts = base.split('_')
    if len(parts) < 2:
        return None
    date_part = parts[0]
    hour_part = parts[1].split('.')[0]
    try:
        _ = datetime.strptime(f"{date_part}T{hour_part}", "%Y-%m-%dT%H")
        return f"{date_part}T{hour_part}"
    except Exception:
        return None


def collect_recent_forecast_dates(region_path: Path, days: int) -> set:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    dates = set()
    for root, _, files in os.walk(region_path):
        for f in files:
            if not f.lower().endswith('.nc'):
                continue
            full = Path(root) / f
            try:
                mtime = datetime.fromtimestamp(full.stat().st_mtime, timezone.utc)
            except Exception:
                continue
            if mtime < cutoff:
                continue
            fd = parse_forecast_date_from_filename(f)
            if fd:
                dates.add(fd)
    return dates


def latest_source_mtime_for_forecast(region_path: Path, forecast_date: str) -> float:
    date, hour = forecast_date.split('T')
    prefix = f"{date}_{hour}."
    latest = 0.0
    for root, _, files in os.walk(region_path):
        for f in files:
            if f.startswith(prefix) and f.endswith('.nc'):
                p = Path(root) / f
                try:
                    m = p.stat().st_mtime
                    if m > latest:
                        latest = m
                except Exception:
                    continue
    return latest


def write_cache(prebuilt_dir: Path, func_name: str, region: str, forecast_date: str, result, hash_suffix: str, latest_src: float, dry_run: bool):
    cache_path = make_cache_paths(prebuilt_dir, func_name, region, forecast_date, hash_suffix)
    lock_path = cache_path.with_suffix(cache_path.suffix + '.lock')
    if dry_run:
        print(f"[DRY] Would write {cache_path.name}")
        return
    if not acquire_lock(lock_path, timeout=5.0):
        print(f"Lock busy: {cache_path.name}")
        return
    try:
        payload = json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_latest_mtime": latest_src,
            "result": result
        }, default=str)
        atomic_write(cache_path, payload)
        print(f"Wrote {cache_path}")
    except Exception as e:
        print(f"Failed write {cache_path}: {e}")
    finally:
        release_lock(lock_path)


def generate_if_needed(data_dir: str, func_name: str, region: str, forecast_date: str, percentile: int, normalize: int, prebuilt_dir: Path, dry_run: bool = False, methods: list | None = None, lead_times: list | None = None):
    prebuilt_dir.mkdir(parents=True, exist_ok=True)
    region_path = resolve_data_dir(data_dir) / region
    if not region_path.exists():
        print(f"Skip region {region}: not found")
        return

    latest_src = latest_source_mtime_for_forecast(region_path, forecast_date)
    if latest_src == 0.0:
        print(f"No sources {region} {forecast_date}")
        return

    def up_to_date(hash_suffix_local):
        cp = make_cache_paths(prebuilt_dir, func_name, region, forecast_date, hash_suffix_local)
        return cp.exists() and cp.stat().st_mtime >= latest_src

    base_dir_resolved = resolve_data_dir(data_dir)
    base_dir_resolved = base_dir_resolved.absolute().as_posix()

    if func_name == 'series_synthesis_per_method':
        hash_suffix = compute_cache_hash(func_name, region, forecast_date, percentile, normalize)
        if up_to_date(hash_suffix):
            print(f"Up-to-date: series_synthesis_per_method {region} {forecast_date}")
            return
        print(f"Build series_synthesis_per_method {region} {forecast_date}")
        result = agg_svc._get_series_synthesis_per_method(base_dir_resolved, region, forecast_date, percentile, normalize)
        write_cache(prebuilt_dir, func_name, region, forecast_date, result, hash_suffix, latest_src, dry_run)
        return

    if func_name == 'series_synthesis_total':
        hash_suffix = compute_cache_hash(func_name, region, forecast_date, percentile, normalize)
        if up_to_date(hash_suffix):
            print(f"Up-to-date: series_synthesis_total {region} {forecast_date}")
            return
        print(f"Build series_synthesis_total {region} {forecast_date}")
        result = agg_svc._get_series_synthesis_total(base_dir_resolved, region, forecast_date, percentile, normalize)
        write_cache(prebuilt_dir, func_name, region, forecast_date, result, hash_suffix, latest_src, dry_run)
        return

    if func_name == 'list_methods':
        hash_suffix = compute_cache_hash(func_name, region, forecast_date)
        if up_to_date(hash_suffix):
            print(f"Up-to-date: list_methods {region} {forecast_date}")
            return
        print(f"Build list_methods {region} {forecast_date}")
        result = meta_svc._get_methods_from_netcdf(base_dir_resolved, region, forecast_date)
        write_cache(prebuilt_dir, func_name, region, forecast_date, result, hash_suffix, latest_src, dry_run)
        return

    if func_name == 'list_methods_and_configs':
        hash_suffix = compute_cache_hash(func_name, region, forecast_date)
        if up_to_date(hash_suffix):
            print(f"Up-to-date: list_methods_and_configs {region} {forecast_date}")
            return
        print(f"Build list_methods_and_configs {region} {forecast_date}")
        result = meta_svc._get_method_configs_from_netcdf(base_dir_resolved, region, forecast_date)
        write_cache(prebuilt_dir, func_name, region, forecast_date, result, hash_suffix, latest_src, dry_run)
        return

    if func_name == 'entities_analog_values_percentile':
        if methods is None:
            methods_data = meta_svc._get_methods_from_netcdf(base_dir_resolved, region, forecast_date)
            methods_local = [m['id'] for m in methods_data.get('methods', [])]
        else:
            methods_local = methods
        if lead_times is None:
            lead_times_local = [24, 48, 72]
        else:
            lead_times_local = lead_times
        for method in methods_local:
            for lt in lead_times_local:
                hash_suffix = compute_cache_hash(func_name, region, forecast_date, percentile, normalize, method=method, lead_time=lt)
                if up_to_date(hash_suffix):
                    print(f"Up-to-date: entities_analog_values_percentile {region} {forecast_date} m={method} lt={lt}")
                    continue
                print(f"Build entities_analog_values_percentile {region} {forecast_date} m={method} lt={lt}")
                try:
                    result = agg_svc._get_entities_analog_values_percentile(base_dir_resolved, region, forecast_date, method, lt, percentile, normalize)
                except Exception as e:
                    print(f"Failed m={method} lt={lt}: {e}")
                    continue
                write_cache(prebuilt_dir, func_name, region, forecast_date, result, hash_suffix, latest_src, dry_run)
        return

    print(f"Unknown function: {func_name}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warm up prebuilt JSON caches for heavy endpoints")
    parser.add_argument("--data-dir", default="/app/data", help="Path to data directory")
    parser.add_argument("--days", type=int, default=10, help="Look back N days")
    parser.add_argument("--functions", nargs='+', default=['series_synthesis_per_method','series_synthesis_total'], help="Functions to warm (add: list_methods list_methods_and_configs entities_analog_values_percentile)")
    parser.add_argument("--regions", nargs='*', help="Subset of regions")
    parser.add_argument("--percentile", type=int, default=90, help="Percentile (for percentile-based funcs)")
    parser.add_argument("--normalize", type=int, default=10, help="Normalization reference")
    parser.add_argument("--methods", nargs='*', help="Limit methods for entities_analog_values_percentile")
    parser.add_argument("--lead-times", default="0,24,48,72", help="Comma list of lead times for entities_analog_values_percentile")
    parser.add_argument("--dry-run", action='store_true', help="Only show actions")
    args = parser.parse_args(argv)

    prebuilt_dir = resolve_data_dir(args.data_dir) / '.prebuilt_cache'

    lead_times = [int(x) for x in args.lead_times.split(',') if x.strip().isdigit()]

    base = resolve_data_dir(args.data_dir)
    regions = [p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith('.')]
    if args.regions:
        regions = [r for r in regions if r in args.regions]

    for region in regions:
        region_path = base / region
        forecast_dates = collect_recent_forecast_dates(region_path, args.days)
        if not forecast_dates:
            print(f"No recent forecasts for region {region}")
            continue
        for fd in sorted(forecast_dates):
            for func_name in args.functions:
                generate_if_needed(args.data_dir, func_name, region, fd, args.percentile, args.normalize, prebuilt_dir, dry_run=args.dry_run, methods=args.methods, lead_times=lead_times)


if __name__ == '__main__':
    main()
