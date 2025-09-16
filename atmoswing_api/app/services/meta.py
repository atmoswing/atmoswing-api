import xarray as xr
import asyncio
import os

from atmoswing_api.app.utils import utils


async def get_config_data(data_dir: str):
    """
    Get the configuration data from the settings.
    """
    return await asyncio.to_thread(_get_config_data, data_dir)


async def get_last_forecast_date(data_dir: str, region: str):
    """
    Get the last available forecast date for a given region.
    """
    return await asyncio.to_thread(_get_last_forecast_date, data_dir, region)


async def has_forecast_date(data_dir: str, region: str, forecast_date: str):
    """
    Check if forecasts are available for a given region and forecast date.
    """
    return await asyncio.to_thread(_has_forecast_date, data_dir, region,
                                   forecast_date)


async def get_method_list(data_dir: str, region: str, forecast_date: str):
    """
    Get the list of available method types for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    return await asyncio.to_thread(_get_methods_from_netcdf, data_dir, region,
                                   forecast_date)


async def get_method_configs_list(data_dir: str, region: str, forecast_date: str):
    """
    Get the list of available method types and configurations for a given region.
    Simulate async reading by using asyncio to run blocking I/O functions
    """
    return await asyncio.to_thread(_get_method_configs_from_netcdf, data_dir, region,
                                   forecast_date)


async def get_entities_list(data_dir: str, region: str, forecast_date: str, method: str,
                            configuration: str):
    """
    Get the list of available entities for a given region, forecast_date, method, and configuration.
    """
    return await asyncio.to_thread(_get_entities_from_netcdf, data_dir, region,
                                   forecast_date, method, configuration)


async def get_relevant_entities_list(data_dir: str, region: str, forecast_date: str,
                                     method: str, configuration: str):
    """
    Get the list of relevant entities for a given region, forecast_date, method, and configuration.
    """
    return await asyncio.to_thread(_get_relevant_entities_from_netcdf, data_dir,
                                   region, forecast_date, method, configuration)


def _get_config_data(data_dir: str):
    """
    Synchronous function to get the configuration data from the settings.
    """
    regions_list = []
    errors = []

    # List the regions (directories) in the data directory
    try:
        regions_list = [d for d in os.listdir(data_dir) if
                        os.path.isdir(os.path.join(data_dir, d))]
    except FileNotFoundError:
        errors.append(f"Data directory not found: {data_dir}")

    return {
        "data_dir": data_dir,
        "regions": regions_list,
        "errors": errors
    }

def _get_last_forecast_date(data_dir: str, region: str):
    """
    Synchronous function to get the last forecast date from the filenames.
    Directory structure: region_path/YYYY/MM/DD/YYYY-MM-DD_HH.method.region.nc
    """
    return {
        "parameters" : {
            "region": region
        },
        "last_forecast_date": utils.get_last_forecast_date(data_dir, region)
    }


def _has_forecast_date(data_dir: str, region: str, forecast_date: str):
    region_path = utils.check_region_path(data_dir, region)

    # Synchronous function to get methods from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    try:
        files = utils.list_files(region_path, forecast_date)
        has_forecasts = len(files) > 0
    except FileNotFoundError:
        has_forecasts = False

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
        },
        "has_forecasts": has_forecasts
    }


def _get_methods_from_netcdf(data_dir: str, region: str, forecast_date: str):
    region_path = utils.check_region_path(data_dir, region)

    # Synchronous function to get methods from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    files = utils.list_files(region_path, forecast_date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {forecast_date}")

    methods = []

    # Open the NetCDF files and get the method IDs and names
    for file in files:
        with xr.open_dataset(file, engine="h5netcdf") as ds:
            method_id = ds.method_id
            method_name = utils.decode_surrogate_escaped_utf8(ds.method_id_display)
            if not any(method['id'] == method_id for method in methods):
                methods.append({"id": method_id, "name": method_name})

    methods.sort(key=lambda x: x['id'])

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
        },
        "methods": methods
    }


def _get_method_configs_from_netcdf(data_dir: str, region: str, forecast_date: str):
    region_path = utils.check_region_path(data_dir, region)

    # Synchronous function to get method configurations from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    files = utils.list_files(region_path, forecast_date)

    # Check that the files exist
    if not files:
        raise FileNotFoundError(f"No files found for date: {forecast_date}")

    method_configs = []

    # Open the NetCDF files and get the method IDs and configurations
    for file in files:
        with xr.open_dataset(file, engine="h5netcdf") as ds:
            method_id = ds.method_id
            method_name = utils.decode_surrogate_escaped_utf8(ds.method_id_display)
            config_id = ds.specific_tag
            config_name = utils.decode_surrogate_escaped_utf8(ds.specific_tag_display)
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

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date)
        },
        "methods": method_configs
    }


def _get_entities_from_netcdf(data_dir: str, region: str, forecast_date: str, method: str,
                              configuration: str):
    region_path = utils.check_region_path(data_dir, region)

    # Synchronous function to get entities from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    entities = []

    # Open the NetCDF files and get the entities
    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        station_ids = ds.station_ids.values
        station_official_ids = ds.station_official_ids.values
        station_names = ds.station_names.values
        station_x_coords = ds.station_x_coords.values
        station_y_coords = ds.station_y_coords.values

        # Create a list of dictionaries with the entity information
        for i in range(len(station_ids)):
            entity = {
                "id": int(station_ids[i]),
                "name": utils.decode_surrogate_escaped_utf8(str(station_names[i])),
                "x": float(station_x_coords[i]),
                "y": float(station_y_coords[i])
            }

            if station_official_ids[i]:
                entity["official_id"] = str(station_official_ids[i])

            entities.append(entity)

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration
        },
        "entities": entities
    }


def _get_relevant_entities_from_netcdf(data_dir: str, region: str, forecast_date: str,
                                        method: str, configuration: str):
    """
    Get the list of relevant entities for a given region, forecast_date, method, and configuration.
    """
    region_path = utils.check_region_path(data_dir, region)

    # Synchronous function to get entities from the NetCDF file
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    entities = []

    # Open the NetCDF files and get the entities
    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        station_ids = ds.station_ids.values
        station_official_ids = ds.station_official_ids.values
        station_names = ds.station_names.values
        station_x_coords = ds.station_x_coords.values
        station_y_coords = ds.station_y_coords.values

        # Create a list of dictionaries with the entity information
        relevant_idx = utils.get_relevant_stations_idx(ds)
        for i in relevant_idx:
            entity = {
                "id": int(station_ids[i]),
                "name": utils.decode_surrogate_escaped_utf8(str(station_names[i])),
                "x": float(station_x_coords[i]),
                "y": float(station_y_coords[i])
            }

            if station_official_ids[i]:
                entity["official_id"] = str(station_official_ids[i])

            entities.append(entity)

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration
        },
        "entities": entities
    }