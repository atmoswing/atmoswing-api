import os
import glob
import numpy as np
from datetime import datetime, date


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

def get_files_pattern(region_path: str, datetime_str: str) -> str:
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_pattern = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}*.nc"

    return f"{path}/{file_pattern}"


def list_files(region_path: str, datetime_str: str) -> list:
    full_pattern = get_files_pattern(region_path, datetime_str)

    files = sorted(glob.glob(full_pattern))

    return files


def get_file_path(region_path: str, datetime_str: str, method: str, configuration: str) -> str:
    dt = convert_to_datetime(datetime_str)
    path = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Date directory not found: {path}")

    file_path = f"{path}/{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.{configuration}.nc"

    return file_path


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
