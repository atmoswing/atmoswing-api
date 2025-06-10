import os
import glob
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta


def check_region_path(data_dir: str, region: str) -> str:
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
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format ({date_str})")


def convert_to_datetime(datetime_str: str) -> datetime:
    if isinstance(datetime_str, datetime):
        return datetime_str

    try:
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H")
    except ValueError:
        dt = convert_to_date(datetime_str)
        return datetime(dt.year, dt.month, dt.day)


def convert_to_target_date(forecast_date, lead_time) -> datetime:
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
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_pattern = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.*.nc"

    return f"{path}/{file_pattern}"


def get_last_forecast_date(data_dir: str, region: str):
    """
    Get the last forecast date from the filenames.
    Directory structure: region_path/YYYY/MM/DD/YYYY-MM-DD_HH.method.region.nc
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
    full_pattern = get_files_pattern(region_path, datetime_str)

    files = sorted(glob.glob(full_pattern))

    return files


def get_file_path(region_path: str, datetime_str: str, method: str,
                  configuration: str) -> str:
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_path = f"{path}/{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.{configuration}.nc"

    return file_path


def get_row_indices(ds, target_date):
    # Get the start and end indices for the entity
    target_date_idx, target_date = get_target_date_index(ds, target_date)
    analogs_nb = ds.analogs_nb.values
    start_idx = int(np.sum(analogs_nb[:target_date_idx]))
    end_idx = start_idx + int(analogs_nb[target_date_idx])
    return start_idx, end_idx, target_date


def get_target_date_index(ds, target_date):
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
    target_date_found: datetime
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
            target_date_idx = i
            target_date_found = date
            break
        elif date < target_date:
            target_date_idx = i
            target_date_found = date
        elif date > target_date:
            break

    return target_date_idx, target_date_found


def compute_lead_time(forecast_date, target_date):
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


def get_entity_index(ds, entity):
    # Find the entity ID
    station_ids = ds.station_ids.values
    indices = np.where(station_ids == entity)[0]
    entity_idx = int(indices[0]) if indices.size > 0 else -1
    if entity_idx == -1:
        raise ValueError(f"Entity not found: {entity}")
    return entity_idx


def build_cumulative_frequency(size):
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
