import xarray as xr
import asyncio
import os
import dask

from ..utils import utils


async def get_method_list(data_dir: str, region: str, date: str):
    """
    Get the list of available method types for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    region_path = utils.check_region_path(data_dir, region)
    methods = await asyncio.to_thread(_get_methods_from_netcdf, region_path, date)

    return {"methods": methods}


async def get_last_forecast_date_from_files(data_dir: str, region: str):
    """
    Get the last available forecast date for a given region.
    """
    region_path = utils.check_region_path(data_dir, region)
    last_forecast_date = await asyncio.to_thread(_get_last_forecast_date, region_path)

    return {"last_forecast_date": last_forecast_date}


def _get_methods_from_netcdf(region_path: str, date: str):
    # Synchronous function to get methods from the NetCDF file
    if date == 'latest':
        date = _get_last_forecast_date(region_path)

    files = utils.list_files(region_path, date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {date}")

    methods = []

    # Open the NetCDF files and get the method IDs and names
    for file in files:
        with xr.open_dataset(file) as ds:
            # Skip if already in the list
            if ds.method_id in [method[0] for method in methods]:
                continue
            methods.extend(list(set(zip([ds.method_id], [ds.method_id_display]))))

    # Sort the methods by ID
    methods.sort(key=lambda x: x[0])

    return methods


def _get_last_forecast_date(region_path: str):
    """
    Synchronous function to get the last forecast date from the filenames.
    Directory structure: region_path/YYYY/MM/DD/YYYY-MM-DD_HH.method.region.nc
    """
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
    _ = utils.convert_to_datetime(last_forecast_date)

    return last_forecast_date

