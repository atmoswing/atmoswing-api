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


async def get_method_configs_list(data_dir: str, region: str, date: str):
    """
    Get the list of available method types and configurations for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    region_path = utils.check_region_path(data_dir, region)
    method_configs = await asyncio.to_thread(_get_method_configs_from_netcdf, region_path, date)

    return {"method_configs": method_configs}


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
            method_id = ds.method_id
            method_name = ds.method_id_display
            if not any(method['id'] == method_id for method in methods):
                methods.append({"id": method_id, "name": method_name})

    methods.sort(key=lambda x: x['id'])

    return methods


def _get_method_configs_from_netcdf(region_path: str, date: str):
    # Synchronous function to get method configurations from the NetCDF file
    if date == 'latest':
        date = _get_last_forecast_date(region_path)

    files = utils.list_files(region_path, date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {date}")

    method_configs = []

    # Open the NetCDF files and get the method IDs and configurations
    for file in files:
        with xr.open_dataset(file) as ds:
            method_id = ds.method_id
            method_name = ds.method_id_display
            config_id = ds.specific_tag
            config_name = ds.specific_tag_display
            for method in method_configs:
                if method['id'] == method_id:
                    method['configurations'].append(
                        {"id": config_id, "name": config_name})
                    break
            else:
                method_configs.append(
                    {"id": method_id, "name": method_name,
                     "configurations": [{"id": config_id, "name": config_name}]})

    # Sort the method configurations by ID
    method_configs.sort(key=lambda x: x['id'])

    return method_configs


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

