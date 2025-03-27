import os
import glob

import xarray as xr
import numpy as np
import asyncio

from ..utils import utils


async def get_entities_analog_values_percentile(data_dir: str, region: str,
                                                forecast_date: str, method: str,
                                                target_date: str, percentile: int):
    """
    Get the precipitation values for a given region, date, method, configuration,
    target date, and percentile.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_entities_analog_values_percentile,
                                   region_path, forecast_date, method,
                                   target_date, percentile)



def _get_entities_analog_values_percentile(region_path: str, forecast_date: str,
                                           method: str, target_date: str,
                                           percentile: int):
    """
    Synchronous function to get the precipitation values for a specific percentile
    from the netCDF file.
    """
    pattern = utils.get_files_pattern(region_path, forecast_date, method)
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    all_station_ids = None
    values = None

    for file_path in files:

        with xr.open_dataset(file_path) as ds:
            # Select the relevant stations
            relevant_station_ids = ds.predictand_station_ids
            relevant_station_ids = [int(x) for x in relevant_station_ids.split(",")]
            if all_station_ids is None:
                all_station_ids = ds.station_ids.values.tolist()
            else:
                assert all_station_ids == ds.station_ids.values.tolist()
            station_idx = [all_station_ids.index(x) for x in relevant_station_ids]

            # Extracting the values
            start_idx, end_idx = utils.get_row_indices(ds, target_date)
            if values is None:
                values = np.ones((len(all_station_ids),)) * np.nan
            analog_values = ds.analog_values_raw[station_idx, start_idx:end_idx].astype(float).values
            values_sorted = np.sort(analog_values, axis=1)

            # Compute the percentiles
            n_entities = values_sorted.shape[0]
            n_analogs = values_sorted.shape[1]
            freq = utils.build_cumulative_frequency(n_analogs)

            # Store in the values array
            values[station_idx] = [float(np.interp(percentile / 100, freq, values_sorted[i, :])) for i in
                      range(n_entities)]

    return {"entity_ids": all_station_ids, "values": values.tolist()}