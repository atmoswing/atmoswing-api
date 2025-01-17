import os
import glob
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
        raise ValueError(f"Invalid datetime format ({datetime_str})")


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
