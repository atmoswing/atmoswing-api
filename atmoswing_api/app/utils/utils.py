import os
import glob
import numpy as np
from datetime import datetime, date, timedelta


def check_region_path(data_dir, region) -> str:
    region_path = f"{data_dir}/{region}"
    if not os.path.exists(region_path):
        raise FileNotFoundError(f"Region directory not found: {region}")

    return region_path


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


def convert_to_mjd(date_str: str) -> float:
    try:
        dt = convert_to_datetime(date_str)
    except ValueError:
        dt = convert_to_date(date_str)
        dt = datetime(dt.year, dt.month, dt.day)
    mjd = (dt - datetime(1858, 11, 17)).total_seconds() / 86400.0
    return mjd


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
    target_date_idx = get_target_date_index(ds, target_date)
    analogs_nb = ds.analogs_nb.values
    start_idx = int(np.sum(analogs_nb[:target_date_idx]))
    end_idx = start_idx + int(analogs_nb[target_date_idx])
    return start_idx, end_idx


def get_target_date_index(ds, target_date):
    # Find the lead time
    target_dates = ds.target_dates.values
    target_date = convert_to_datetime(target_date)
    target_date_idx = -1
    for i, date in enumerate(target_dates):
        date = np.datetime64(date).astype('datetime64[s]').item()
        if date == target_date:
            target_date_idx = i
            break
    return target_date_idx


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
