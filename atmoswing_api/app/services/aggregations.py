import os
import glob

import xarray as xr
import numpy as np
import asyncio

from ..utils import utils


async def get_entities_analog_values_percentile(data_dir: str, region: str,
                                                forecast_date: str, method: str,
                                                lead_time: int|str, percentile: int):
    """
    Get the precipitation values for a given region, date, method, configuration,
    target date, and percentile.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_entities_analog_values_percentile,
                                   region_path, forecast_date, method,
                                   lead_time, percentile)


async def get_series_synthesis_per_method(data_dir: str, region: str,
                                          forecast_date: str, percentile: int):
    """
    Get the largest values per method for a given region, date, and percentile.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_series_synthesis_per_method, region_path,
                                   forecast_date, percentile)


async def get_series_synthesis_total(data_dir: str, region: str,
                                     forecast_date: str, percentile: int):
    """
    Get the largest values for a given region, date, and percentile.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_series_synthesis_total, region_path,
                                   forecast_date, percentile)


def _get_entities_analog_values_percentile(region_path: str, forecast_date: str,
                                           method: str, lead_time: int|str,
                                           percentile: int):
    """
    Synchronous function to get the precipitation values for a specific percentile
    from the netCDF file.
    """
    pattern = utils.get_files_pattern(region_path, forecast_date, method)
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    all_station_ids = None
    values = None

    for file_path in files:

        with xr.open_dataset(file_path) as ds:
            # Select the relevant stations
            if all_station_ids is None:
                all_station_ids = ds.station_ids.values.tolist()
            else:
                assert all_station_ids == ds.station_ids.values.tolist()
            station_indices = _get_relevant_stations_idx(ds)

            # Extracting the values
            start_idx, end_idx = utils.get_row_indices(ds, target_date)
            if values is None:
                values = np.ones((len(all_station_ids),)) * np.nan
            analog_values = ds.analog_values_raw[station_indices, start_idx:end_idx].astype(float).values
            values_sorted = np.sort(analog_values, axis=1)

            # Compute the percentiles
            n_entities = values_sorted.shape[0]
            n_analogs = values_sorted.shape[1]
            freq = utils.build_cumulative_frequency(n_analogs)

            # Store in the values array
            values[station_indices] = [float(np.interp(percentile / 100, freq, values_sorted[i, :])) for i in
                      range(n_entities)]

    return {"entity_ids": all_station_ids, "values": values.tolist()}


def _get_series_synthesis_per_method(region_path: str, forecast_date: str,
                                     percentile: int):
    """
    Synchronous function to get the largest analog values for a given region, date,
    and percentile.
    """
    pattern = utils.get_files_pattern(region_path, forecast_date)
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    method_ids = []
    largest_values = []

    for file_path in files:

        with xr.open_dataset(file_path) as ds:
            analogs_nb = ds.analogs_nb.values

            # Select the relevant method
            method_id = ds.method_id
            if method_id not in method_ids:
                method_ids.append(method_id)
                largest_values.append({
                    "method_id": method_id,
                    "target_dates": [np.datetime64(date).astype('datetime64[s]').item()
                                     for date in ds.target_dates.values],
                    "values": np.zeros((len(analogs_nb),)).astype(float).tolist()
                })
            method_idx = method_ids.index(method_id)

            # Select the relevant stations
            station_indices = _get_relevant_stations_idx(ds)

            # Extracting the values
            for lead_time_idx in range(len(analogs_nb)):
                start_idx = int(np.sum(analogs_nb[:lead_time_idx]))
                end_idx = start_idx + int(analogs_nb[lead_time_idx])
                analog_values = ds.analog_values_raw[station_indices, start_idx:end_idx].astype(
                    float).values
                values_sorted = np.sort(analog_values, axis=1)

                # Compute the percentiles
                n_entities = values_sorted.shape[0]
                n_analogs = values_sorted.shape[1]
                freq = utils.build_cumulative_frequency(n_analogs)

                # Store in the values array
                values_percentile = [
                    float(np.interp(percentile / 100, freq, values_sorted[i, :])) for i
                    in range(n_entities)]

                # Store the largest values
                max_percentile = np.max(values_percentile)
                largest_values[method_idx]["values"][lead_time_idx] = float(max(
                    largest_values[method_idx]["values"][lead_time_idx],
                    max_percentile))

    return largest_values


def _get_series_synthesis_total(region_path: str, forecast_date: str,
                                percentile: int):
    """
    Synchronous function to get the largest analog values for a given region, date,
    and percentile.
    """
    largest_values_per_method = _get_series_synthesis_per_method(
        region_path, forecast_date, percentile)

    # Aggregate the values across methods but separate different time steps
    output = []
    time_steps = []
    for method in largest_values_per_method:
        # Get the time steps in hours
        time_step = method["target_dates"][1] - method["target_dates"][0]
        time_step = int(time_step / np.timedelta64(1, 'h'))

        # Check if the time step is already in the output and add it if not
        if time_step not in time_steps:
            time_steps.append(time_step)
            output.append({
                "time_step": time_step,
                "target_dates": method["target_dates"],
                "values": method["values"]
            })
            continue

        # Get the length of the lead times
        lead_time_idx = time_steps.index(time_step)
        len_lt_original = len(output[lead_time_idx]["target_dates"])
        len_lt_new = len(method["target_dates"])

        # First, check the target dates consistency
        for i in range(min(len_lt_new, len_lt_original)):
            if method["target_dates"][i] != output[lead_time_idx]["target_dates"][i]:
                raise ValueError(f"Target dates are not consistent for "
                                 f"time step {time_step}")

        # If more lead time steps are available, update the target dates
        if len_lt_new > len_lt_original:
            output[lead_time_idx]["target_dates"] = method["target_dates"]
            # Add 0 to the values exceeding the original length
            output[lead_time_idx]["values"] += [0] * (len_lt_new - len_lt_original)

        for i in range(len_lt_new):
            output[lead_time_idx]["values"][i] = max(
                output[lead_time_idx]["values"][i],
                method["values"][i])

    return output


def _get_relevant_stations_idx(ds):
    relevant_station_ids = ds.predictand_station_ids
    relevant_station_ids = [int(x) for x in relevant_station_ids.split(",")]
    all_station_ids = ds.station_ids.values.tolist()
    station_idx = [all_station_ids.index(x) for x in relevant_station_ids]
    return station_idx
