import os

import xarray as xr
import numpy as np
import asyncio

from ..utils import utils

async def get_analog_values(data_dir: str, region: str, forecast_date: str, method: str,
                            configuration: str, entity: int, target_date: str):
    """
    Get the precipitation values for a given region, date, method, configuration, and entity.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_analog_values, region_path, forecast_date,
                                   method, configuration, entity, target_date)


def _get_analog_values(region_path: str, forecast_date: str, method: str,
                       configuration: str, entity: int, target_date: str):
    """
    Synchronous function to get the precipitation values from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        # Find the entity ID
        station_ids = ds.station_ids.values
        indices = np.where(station_ids == entity)[0]
        entity_idx = int(indices[0]) if indices.size > 0 else -1
        if entity_idx == -1:
            raise ValueError(f"Entity not found: {entity}")

        # Find the lead time
        target_dates = ds.target_dates.values
        target_date = utils.convert_to_datetime(target_date)
        target_date_idx = -1
        for i, date in enumerate(target_dates):
            date = np.datetime64(date).astype('datetime64[s]').item()
            if date == target_date:
                target_date_idx = i
                break

        # Get the start and end indices for the entity
        analogs_nb = ds.analogs_nb.values
        start_idx = int(np.sum(analogs_nb[:target_date_idx]))
        end_idx = start_idx + int(analogs_nb[target_date_idx])

        values = np.around(
            ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(float),
            decimals=1).tolist()

    return {"values": values}
