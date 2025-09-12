# Warmup script that prebuilds JSON responses for heavy aggregation endpoints.
# The script scans regions and recent forecast dates, compares the latest source
# netCDF modification time to the prebuilt JSON's mtime, and regenerates the JSON
# atomically when needed. It uses a simple lockfile to avoid concurrent writes.

import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

from atmoswing_api.app.services import aggregations as svc
from atmoswing_api.app.utils.utils import compute_cache_hash, make_cache_paths


def resolve_data_dir(data_dir: str) -> Path:
    # If data_dir is relative, resolve it against the repository root so './data' works
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
        # validate
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
    # Find files matching the forecast_date prefix (YYYY-MM-DD_HH)
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


def generate_if_needed(data_dir: str, func_name: str, region: str, forecast_date: str, percentile: int, normalize: int, prebuilt_dir: Path, dry_run: bool = False):
    prebuilt_dir.mkdir(parents=True, exist_ok=True)
    hash_suffix = compute_cache_hash(func_name, region, forecast_date, percentile, normalize)
    cache_path = make_cache_paths(prebuilt_dir, func_name, region, forecast_date, hash_suffix)
    lock_path = cache_path.with_suffix(cache_path.suffix + ".lock")

    # Determine latest source mtime
    region_path = Path(resolve_data_dir(data_dir)) / region
    if not region_path.exists():
        print(f"Skipping region {region}: not found")
        return

    latest_src = latest_source_mtime_for_forecast(region_path, forecast_date)
    if latest_src == 0.0:
        print(f"No source files for {region} {forecast_date}; skipping")
        return

    cache_mtime = cache_path.stat().st_mtime if cache_path.exists() else 0.0
    if cache_mtime >= latest_src:
        print(f"Up-to-date: {cache_path.name}")
        return

    print(f"Regenerating cache for {region} {forecast_date} -> {cache_path.name}")
    if dry_run:
        return

    # Acquire lock
    if not acquire_lock(lock_path, timeout=5.0):
        print(f"Could not acquire lock for {cache_path.name}; skipping")
        return

    try:
        # Call the appropriate synchronous service function
        data_dir = resolve_data_dir(data_dir)
        if func_name == 'series_synthesis_per_method':
            result = svc._get_series_synthesis_per_method(data_dir, region, forecast_date, percentile, normalize)
        elif func_name == 'series_synthesis_total':
            result = svc._get_series_synthesis_total(data_dir, region, forecast_date, percentile, normalize)
        else:
            print(f"Unknown function: {func_name}")
            return

        payload = json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_latest_mtime": latest_src,
            "result": result
        }, default=str)

        atomic_write(cache_path, payload)
        print(f"Wrote {cache_path}")
    except Exception as e:
        print(f"Failed to generate cache for {region} {forecast_date}: {e}")
    finally:
        release_lock(lock_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warm up prebuilt JSON caches for heavy aggregation endpoints")
    parser.add_argument("--data-dir", default="/app/data", help="Path to the data directory")
    parser.add_argument("--days", type=int, default=20, help="Look back this many days (default: 20)")
    parser.add_argument("--functions", nargs='+', default=['series_synthesis_per_method', 'series_synthesis_total'], help="Functions to warm")
    parser.add_argument("--regions", nargs='*', help="Limit to specific regions (optional)")
    parser.add_argument("--percentile", type=int, default=90, help="Percentile to use when generating (default: 95)")
    parser.add_argument("--normalize", type=int, default=10, help="Normalize value (default: 10)")
    parser.add_argument("--dry-run", action='store_true', help="Don't write files, just show what would be done")
    args = parser.parse_args(argv)

    prebuilt_dir = Path(resolve_data_dir(args.data_dir)) / '.prebuilt_cache'

    # Iterate regions
    base = Path(resolve_data_dir(args.data_dir))
    regions = [p.name for p in base.iterdir() if p.is_dir()]
    if args.regions:
        regions = [r for r in regions if r in args.regions]

    # Remove directories that are not regions (starting with a dot)
    regions = [r for r in regions if not r.startswith('.')]

    for region in regions:
        region_path = base / region
        forecast_dates = collect_recent_forecast_dates(region_path, args.days)
        if not forecast_dates:
            print(f"No recent forecasts for region {region}")
            continue
        for fd in sorted(forecast_dates):
            for func_name in args.functions:
                generate_if_needed(args.data_dir, func_name, region, fd, args.percentile, args.normalize, prebuilt_dir, dry_run=args.dry_run)


if __name__ == '__main__':
    main()


