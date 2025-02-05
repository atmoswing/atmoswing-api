import xarray as xr
import asyncio
import os

from ..utils import utils


async def get_last_forecast_date_from_files(data_dir: str, region: str):
    """
    Get the last available forecast date for a given region.
    """
    region_path = utils.check_region_path(data_dir, region)
    last_forecast_date = await asyncio.to_thread(_get_last_forecast_date, region_path)

    return {"last_forecast_date": last_forecast_date}


async def get_method_list(data_dir: str, region: str, forecast_date: str):
    """
    Get the list of available method types for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_methods_from_netcdf, region_path,
                                   forecast_date)


async def get_method_configs_list(data_dir: str, region: str, forecast_date: str):
    """
    Get the list of available method types and configurations for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_method_configs_from_netcdf, region_path,
                                   forecast_date)


async def get_entities_list(data_dir: str, region: str, forecast_date: str, method: str,
                            configuration: str):
    """
    Get the list of available entities for a given region, forecast_date, method, and configuration.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_entities_from_netcdf, region_path,
                                   forecast_date, method, configuration)


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


def _get_methods_from_netcdf(region_path: str, forecast_date: str):
    # Synchronous function to get methods from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = _get_last_forecast_date(region_path)

    files = utils.list_files(region_path, forecast_date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {forecast_date}")

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


def _get_method_configs_from_netcdf(region_path: str, forecast_date: str):
    # Synchronous function to get method configurations from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = _get_last_forecast_date(region_path)

    files = utils.list_files(region_path, forecast_date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {forecast_date}")

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


def _get_entities_from_netcdf(region_path: str, forecast_date: str, method: str,
                              configuration: str):
    # Synchronous function to get entities from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = _get_last_forecast_date(region_path)

    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    entities = []

    # Open the NetCDF files and get the entities
    with xr.open_dataset(file_path) as ds:
        station_ids = ds.station_ids.values
        station_official_ids = ds.station_official_ids.values
        station_names = ds.station_names.values
        station_x_coords = ds.station_x_coords.values
        station_y_coords = ds.station_y_coords.values

        # Create a list of dictionaries with the entity information
        for i in range(len(station_ids)):
            entity = {
                "id": int(station_ids[i]),
                "name": str(station_names[i]),
                "x": float(station_x_coords[i]),
                "y": float(station_y_coords[i])
            }

            if station_official_ids[i]:
                entity["official_id"] = str(station_official_ids[i])

            entities.append(entity)

    return entities
