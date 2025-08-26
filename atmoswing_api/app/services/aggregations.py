import os
import glob

import xarray as xr
import numpy as np
import asyncio

from atmoswing_api.app.utils import utils


async def get_entities_analog_values_percentile(
        data_dir: str, region: str, forecast_date: str, method: str, lead_time: int|str,
        percentile: int, normalize: int = 10):
    """
    Get the precipitation values for a given region, date, method, configuration,
    target date, and percentile.
    """
    return await asyncio.to_thread(_get_entities_analog_values_percentile,
                                   data_dir, region, forecast_date, method,
                                   lead_time, percentile, normalize)


async def get_series_synthesis_per_method(
        data_dir: str, region: str, forecast_date: str, percentile: int,
        normalize: int = 10):
    """
    Get the largest values per method for a given region, date, and percentile.
    """
    return await asyncio.to_thread(_get_series_synthesis_per_method, data_dir, region,
                                   forecast_date, percentile, normalize)


async def get_series_synthesis_total(
        data_dir: str, region: str, forecast_date: str, percentile: int,
        normalize: int = 10):
    """
    Get the largest values for a given region, date, and percentile.
    """
    return await asyncio.to_thread(_get_series_synthesis_total, data_dir, region,
                                   forecast_date, percentile, normalize)


def _get_entities_analog_values_percentile(
        data_dir: str, region: str, forecast_date: str, method: str, lead_time: int|str,
        percentile: int, normalize: int = 10):
    """
    Synchronous function to get the precipitation values for a specific percentile
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    pattern = utils.get_files_pattern(region_path, forecast_date, method)
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    all_station_ids = None
    values = None
    values_normalized = None

    for file_path in files:

        with xr.open_dataset(file_path, engine="h5netcdf") as ds:
            # Select the relevant stations
            if all_station_ids is None:
                all_station_ids = ds.station_ids.values.tolist()
            else:
                assert all_station_ids == ds.station_ids.values.tolist()
            station_indices = utils.get_relevant_stations_idx(ds)

            # Extracting the values
            row_indices = utils.get_row_indices(ds, target_date)
            if row_indices is None:
                values = []
                values_normalized = []
                break
            else:
                start_idx, end_idx, target_date = row_indices
                if values is None:
                    values = np.ones((len(all_station_ids),)) * np.nan
                    values_normalized = np.ones((len(all_station_ids),)) * np.nan
                analog_values = ds.analog_values_raw[station_indices, start_idx:end_idx].astype(float).values
                values_sorted = np.sort(analog_values, axis=1)

                # Compute the percentiles
                n_entities = values_sorted.shape[0]
                n_analogs = values_sorted.shape[1]
                freq = utils.build_cumulative_frequency(n_analogs)

                # Store in the values array
                values[station_indices] = [float(np.interp(percentile / 100, freq, values_sorted[i, :])) for i in
                          range(n_entities)]

                # Normalize the values
                ref_values = _get_reference_values(ds, normalize, station_indices)
                values_normalized[station_indices] = values[station_indices] / ref_values

    if isinstance(values, np.ndarray):
        values = values.tolist()
    if isinstance(values_normalized, np.ndarray):
        values_normalized = values_normalized.tolist()

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "percentile": percentile,
            "normalize": normalize
        },
        "entity_ids": all_station_ids,
        "values": values,
        "values_normalized": values_normalized
    }


def _get_series_synthesis_per_method(data_dir: str, region: str, forecast_date: str,
                                     percentile: int, normalize: int = 10):
    """
    Synchronous function to get the largest analog values for a given region, date,
    and percentile.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    pattern = utils.get_files_pattern(region_path, forecast_date)
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    method_ids = []
    largest_values = []

    for file_path in files:

        with xr.open_dataset(file_path, engine="h5netcdf") as ds:
            analogs_nb = ds.analogs_nb.values

            # Select the relevant method
            method_id = ds.method_id
            if method_id not in method_ids:
                method_ids.append(method_id)
                largest_values.append({
                    "method_id": method_id,
                    "target_dates": [np.datetime64(date).astype('datetime64[s]').item()
                                     for date in ds.target_dates.values],
                    "values": np.zeros((len(analogs_nb),)).astype(float).tolist(),
                    "values_normalized": np.zeros((len(analogs_nb),)).astype(float).tolist()
                })
            method_idx = method_ids.index(method_id)

            # Select the relevant stations
            station_indices = utils.get_relevant_stations_idx(ds)

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

                # Normalize the values
                ref_values = _get_reference_values(ds, normalize, station_indices)
                values_normalized = np.array(values_percentile) / ref_values

                # Store the largest values
                largest_values[method_idx]["values"][lead_time_idx] = float(max(
                    largest_values[method_idx]["values"][lead_time_idx],
                    np.max(values_percentile)))

                # Store the normalized values
                largest_values[method_idx]["values_normalized"][lead_time_idx] = float(max(
                    largest_values[method_idx]["values_normalized"][lead_time_idx],
                    np.max(values_normalized)))

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "percentile": percentile,
            "normalize": normalize
        },
        "series_percentiles": largest_values
    }


def _get_series_synthesis_total(data_dir: str, region: str, forecast_date: str,
                                percentile: int, normalize: int = 10):
    """
    Synchronous function to get the largest analog values for a given region, date,
    and percentile.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    largest_values_per_method = _get_series_synthesis_per_method(
        data_dir, region, forecast_date, percentile, normalize)
    largest_values_per_method = largest_values_per_method["series_percentiles"]

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
                "values": method["values"],
                "values_normalized": method["values_normalized"]
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
            output[lead_time_idx]["values_normalized"] += [0] * (len_lt_new - len_lt_original)

        for i in range(len_lt_new):
            output[lead_time_idx]["values"][i] = max(
                output[lead_time_idx]["values"][i],
                method["values"][i])
            output[lead_time_idx]["values_normalized"][i] = max(
                output[lead_time_idx]["values_normalized"][i],
                method["values_normalized"][i])

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "percentile": percentile,
            "normalize": normalize
        },
        "series_percentiles": output
    }


def _get_reference_values(ds, normalize, station_indices):
    axis = ds.reference_axis.values.tolist()
    try:
        ref_idx = axis.index(normalize)
    except ValueError:
        raise ValueError(f"normalize must be in {axis}")

    ref_values = ds.reference_values[station_indices, ref_idx].astype(
        float).values

    return ref_values