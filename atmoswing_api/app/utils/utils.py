import re
import os
import glob
import hashlib
import xarray
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta

def check_region_path(data_dir: str, region: str) -> str:
    """
    Check if the region path exists and is a symlink.
    If it is a symlink, resolve it to the actual path.
    If the path does not exist, raise a FileNotFoundError.

    Parameters
    ----------
    data_dir: str
        The base directory where the region directories are located.
    region: str
        The name of the region directory to check.

    Returns
    -------
    str
        The resolved path to the region directory.
    """
    region_path = Path(data_dir) / region
    region_path = region_path.resolve(strict=False)

    if region_path.is_symlink():
        if not region_path.exists():
            raise FileNotFoundError(f"Broken symlink: {region_path}")
        else:
            return str(region_path)

    if not region_path.exists():
        raise FileNotFoundError(f"Region directory not found: {region_path}")

    return str(region_path)


def convert_to_date(date_str: str) -> date:
    """
    Convert a date string in the format "YYYY-MM-DD" to a date object.
    If the string is already a date object, it will be returned as is.

    Parameters
    ----------
    date_str: str
        The date string to convert.

    Returns
    -------
    date
        The converted date object.
    """
    if isinstance(date_str, date):
        return date_str

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format ({date_str})")


def convert_to_datetime(datetime_str: str) -> datetime:
    """
    Convert a datetime string in the format "YYYY-MM-DDTHH" to a datetime object.
    If the string is already a datetime object, it will be returned as is.

    Parameters
    ----------
    datetime_str: str or datetime
        The datetime string to convert.

    Returns
    -------
    datetime
        The converted datetime object.
    """
    if isinstance(datetime_str, datetime):
        return datetime_str

    try:
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H")
    except ValueError:
        dt = convert_to_date(datetime_str)
        return datetime(dt.year, dt.month, dt.day)


def convert_to_target_date(forecast_date, lead_time) -> datetime:
    """
    Convert the lead time to a target date based on the forecast date.
    If the lead time is a string, it will be interpreted as a datetime string.
    If the lead time is an integer, it will be interpreted as hours to add to the
    forecast date.
    If the lead time is already a datetime object, it will be returned as is.

    Parameters
    ----------
    forecast_date: str or datetime
        The forecast date to use as a base for the lead time.
    lead_time: str, int, or datetime
        The lead time to convert to a target date. It can be a string (datetime format),
        an integer (number of hours), or a datetime object.

    Returns
    -------
    datetime
        The target date calculated from the forecast date and lead time.
    """
    forecast_date = convert_to_datetime(forecast_date)

    if isinstance(lead_time, datetime):
        return lead_time

    if isinstance(lead_time, str):
        try:
            target_date = convert_to_datetime(lead_time)
            return target_date
        except Exception as e:
            dt = int(lead_time)  # in hours
            target_date = forecast_date + timedelta(hours=dt)
            return target_date

    if isinstance(lead_time, int):
        target_date = forecast_date + timedelta(hours=lead_time)
        return target_date

    raise ValueError(f"Invalid lead time format ({lead_time})")


def get_files_pattern(region_path: str, datetime_str: str, method='*') -> str:
    """
    Get the file pattern for a given region path and datetime string.
    The expected directory structure is:
    region_path/YYYY/MM/DD/YYYY-MM-DD_HH.method.*.nc

    Parameters
    ----------
    region_path: str
        The path to the region directory.
    datetime_str: str
        The datetime string in the format "YYYY-MM-DDTHH" or "YYYY-MM-DD".
    method: str
        The method to filter the files by. Default is '*', which matches all methods.

    Returns
    -------
    str
        The file pattern to search for in the region directory.
    """
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_pattern = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.*.nc"

    return f"{path}/{file_pattern}"


def get_last_forecast_date(data_dir: str, region: str) -> str:
    """
    Get the last forecast date from the filenames.
    Directory structure: region_path/YYYY/MM/DD/YYYY-MM-DD_HH.method.region.nc

    Parameters
    ----------
    data_dir: str
        The base directory where the region directories are located.
    region: str
        The name of the region directory to check.

    Returns
    -------
    str
        The last forecast date in the format "YYYY-MM-DDTHH".
    """
    region_path = check_region_path(data_dir, region)

    def get_latest_subdir(path):
        subdirs = sorted(os.listdir(path), reverse=True)
        if not subdirs:
            raise ValueError(f"No subdirectories found in {path}")
        return subdirs[0]

    # Get the latest year, month, and day
    year = get_latest_subdir(region_path)
    month = get_latest_subdir(f"{region_path}/{year}")
    day = get_latest_subdir(f"{region_path}/{year}/{month}")

    # Get the latest file
    files = sorted(os.listdir(f"{region_path}/{year}/{month}/{day}"), reverse=True)
    if not files:
        raise ValueError(f"No files found in {region_path}/{year}/{month}/{day}")

    # Extract the hour from the latest file
    last_file = files[0]
    parts = last_file.split("_")
    if len(parts) < 2:
        raise ValueError(f"Invalid file format ({last_file})")
    hour = parts[1].split(".")[0]

    last_forecast_date = f"{year}-{month}-{day}T{hour}"

    # Check that the forecast date is valid
    _ = convert_to_datetime(last_forecast_date)

    return last_forecast_date


def list_files(region_path: str, datetime_str: str) -> list:
    """
    List all files in the region path for a given datetime string.

    Parameters
    ----------
    region_path: str
        The path to the region directory.
    datetime_str: str
        The datetime string in the format "YYYY-MM-DDTHH" or "YYYY-MM-DD".

    Returns
    -------
    list
        A sorted list of file paths matching the pattern for the given datetime.
    """
    full_pattern = get_files_pattern(region_path, datetime_str)

    files = sorted(glob.glob(full_pattern))

    return files


def get_file_path(
        region_path: str,
        datetime_str: str,
        method: str,
        configuration: str
) -> str:
    """
    Get the file path for a given region, datetime, method, and configuration.

    Parameters
    ----------
    region_path: str
        The path to the region directory.
    datetime_str: str
        The datetime string in the format "YYYY-MM-DDTHH" or "YYYY-MM-DD".
    method: str
        The method to filter the file by.
    configuration: str
        The configuration to filter the file by.

    Returns
    -------
    str
        The full path to the file matching the given parameters.
    """
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_path = f"{path}/{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.{configuration}.nc"

    return file_path


def get_row_indices(
        ds: xarray.Dataset,
        target_date : str | datetime
) -> tuple[int, int, datetime]|None:
    """
    Get the start and end indices for the entity in the dataset based on the target date.
    The target date is used to find the corresponding index in the dataset's target dates.

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset containing the target dates and analogs.
    target_date: str or datetime
        The target date to find in the dataset, can be a string or a datetime object.

    Returns
    -------
    start_idx: int
        The start index of the entity in the dataset.
    end_idx: int
        The end index of the entity in the dataset.
    target_date: datetime
        The date found in the dataset that matches the target date.
    """
    # Get the start and end indices for the entity
    result = get_target_date_index(ds, target_date)
    if result is None:
        return None

    target_date_idx, target_date = result
    analogs_nb = ds.analogs_nb.values
    start_idx = int(np.sum(analogs_nb[:target_date_idx]))
    end_idx = start_idx + int(analogs_nb[target_date_idx])

    return start_idx, end_idx, target_date


def get_target_date_index(
        ds: xarray.Dataset,
        target_date: str | datetime
) -> tuple[int, datetime]|None:
    """
    Finds the index of the target date in the dataset and returns it along with the
    found date.

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset containing the target dates.
    target_date: str or datetime
        The target date to find in the dataset, can be a string or a datetime object.

    Returns
    -------
    target_date_idx: int
        The index of the target date in the dataset.
    target_date_found: datetime|None
        The date found in the dataset that matches the target date.
    """
    # Find the lead time
    target_dates = ds.target_dates.values
    target_date = convert_to_datetime(target_date)
    target_date_idx = -1
    target_date_found = None
    for i, date in enumerate(target_dates):
        date = np.datetime64(date).astype('datetime64[s]').item()
        if date == target_date:
            return i, date
        elif date < target_date:
            if i == len(target_dates) - 1:
                return None
            target_date_idx = i
            target_date_found = date
        elif date > target_date:
            break

    return target_date_idx, target_date_found


def compute_lead_time(forecast_date: datetime, target_date: datetime) -> int:
    """
    Computes the lead time in hours between the forecast date and the target date.

    Parameters
    ----------
    forecast_date: datetime
        The forecast date.
    target_date: datetime
        The target date.

    Returns
    -------
    lead_time: int
        The lead time in hours.
    """
    if isinstance(forecast_date, str):
        forecast_date = convert_to_datetime(forecast_date)
    if isinstance(target_date, str):
        target_date = convert_to_datetime(target_date)

    if not isinstance(forecast_date, datetime) or not isinstance(target_date, datetime):
        raise ValueError("Both forecast_date and target_date must be datetime objects.")

    lead_time = (target_date - forecast_date).total_seconds() / 3600.0

    return int(lead_time)


def get_entity_index(ds: xarray.Dataset, entity: int | str) -> int:
    """
    Get the index of the entity in the dataset based on the entity ID.

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset containing the entity IDs.
    entity: int or str
        The entity ID to find in the dataset.

    Returns
    -------
    entity_idx: int
        The index of the entity in the dataset.
    """
    # Find the entity ID
    station_ids = ds.station_ids.values
    indices = np.where(station_ids == entity)[0]
    entity_idx = int(indices[0]) if indices.size > 0 else -1
    if entity_idx == -1:
        raise ValueError(f"Entity not found: {entity}")

    return entity_idx


def get_relevant_stations_idx(ds):
    """
    Get the indices of the relevant stations in the dataset based on the
    `predictand_station_ids` attribute.

    Parameters
    ----------
    ds: xarray.Dataset
        The forecast dataset.

    Returns
    -------
    station_idx: list
        A list of indices corresponding to the relevant stations in the dataset.
    """
    relevant_station_ids = ds.predictand_station_ids
    relevant_station_ids = [int(x) for x in relevant_station_ids.split(",")]
    all_station_ids = ds.station_ids.values.tolist()
    station_idx = [all_station_ids.index(x) for x in relevant_station_ids]

    return station_idx


def build_cumulative_frequency(size: int) -> np.ndarray:
    """
    Constructs a cumulative frequency distribution.

    Parameters
    ----------
    size: int
        The size of the distribution.

    Returns
    -------
    f: ndarray
        The cumulative frequency distribution.
    """
    # Parameters for the estimated distribution from Gringorten (a=0.44, b=0.12).
    # Choice based on [Cunnane, C., 1978, Unbiased plotting positions—A review:
    # Journal of Hydrology, v. 37, p. 205–222.]
    irep = 0.44
    nrep = 0.12

    divisor = 1.0 / (size + nrep)

    f = np.arange(size, dtype=float)
    f += 1.0 - irep
    f *= divisor

    return f


def sanitize_unicode_surrogates(obj):
    """
    Recursively remove surrogate unicode characters from all strings in a dict/list.
    """
    surrogate_pattern = re.compile(r'[\ud800-\udfff]')
    if isinstance(obj, dict):
        return {k: sanitize_unicode_surrogates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_unicode_surrogates(v) for v in obj]
    elif isinstance(obj, str):
        return surrogate_pattern.sub('', obj)
    else:
        return obj


def decode_surrogate_escaped_utf8(s: str) -> str:
    """Repair strings where UTF-8 bytes were turned into low-surrogate code points
    via the 'surrogateescape' error handler or similar mishandling, e.g.
    'C\udcc3\udca9vennes' -> 'Cévennes'. We rebuild the original byte stream by
    mapping each U+DC80..U+DCFF to its raw byte 0x80..0xFF, while encoding all
    other characters as UTF-8 bytes, then decode once as UTF-8.
    If decoding fails, return the original string.
    """
    if not isinstance(s, str):
        return s
    if not any('\udc80' <= ch <= '\udcff' for ch in s):  # fast path
        return s
    b = bytearray()
    for ch in s:
        code = ord(ch)
        if 0xDC80 <= code <= 0xDCFF:  # surrogateescape preserved byte
            b.append(code - 0xDC00)
        else:
            b.extend(ch.encode('utf-8'))
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return s


def compute_cache_hash(func_name: str, region: str, forecast_date: str, percentile: int | None = None, normalize: int | None = None, **extra) -> str:
    """
    Compute a hash suffix for caching based on core parameters and any additional
    keyword arguments. Backwards compatible with previous signature
    (func_name, region, forecast_date, percentile, normalize).
    Additional uniqueness (e.g. method, lead_time) can be added via **extra.
    """
    parts = [str(func_name), str(region), str(forecast_date)]
    if percentile is not None:
        parts.append(str(percentile))
    if normalize is not None:
        parts.append(str(normalize))
    for k in sorted(extra.keys()):
        parts.append(f"{k}={extra[k]}")
    payload = ":".join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def make_cache_paths(prebuilt_dir: Path, func_name: str, region: str, forecast_date: str, hash_suffix: str) -> Path:
    """
    Create a cache file path based on the function name, region, forecast date,
    and hash suffix.

    Parameters
    ----------
    prebuilt_dir: Path
        The directory where prebuilt cache files are stored.
    func_name: str
        The name of the function for which the cache is being created.
    region: str
        The region identifier.
    forecast_date: str
        The forecast date in string format.
    hash_suffix: str
        The hash suffix for the cache file.

    Returns
    -------
    Path
        The full path to the cache file.
    """
    safe_forecast = forecast_date.replace(':', '-')
    filename = f"{func_name}_{region}_{safe_forecast}_{hash_suffix}.json"
    return prebuilt_dir / filename
