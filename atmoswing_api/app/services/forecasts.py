import os

import xarray as xr
import numpy as np
import asyncio

from atmoswing_api.app.utils import utils


async def get_reference_values(data_dir: str, region: str, forecast_date: str,
                               method: str, configuration: str, entity: int):
    """
    Get the reference values (e.g. for different return periods) for a given region,
    forecast date, method, configuration, and entity.
    """
    return await asyncio.to_thread(_get_reference_values, data_dir, region,
                                   forecast_date, method, configuration, entity)


async def get_analogs(data_dir: str, region: str, forecast_date: str, method: str,
                      configuration: str, entity: int, lead_time: int | str):
    """
    Get the analogs for a given region, forecast date, method, configuration, entity,
    and target date.
    """
    return await asyncio.to_thread(_get_analogs, data_dir, region, forecast_date,
                                   method, configuration, entity, lead_time)


async def get_analog_dates(data_dir: str, region: str, forecast_date: str, method: str,
                           configuration: str, lead_time: int | str):
    """
    Get the analog dates for a given region, date, method, configuration,
    and target date.
    """
    return await asyncio.to_thread(_get_analog_dates, data_dir, region, forecast_date,
                                   method, configuration, lead_time)


async def get_analog_criteria(data_dir: str, region: str, forecast_date: str,
                              method: str, configuration: str, lead_time: int | str):
    """
    Get the analog criteria for a given region, date, method, configuration,
    and target date.
    """
    return await asyncio.to_thread(_get_analog_criteria, data_dir, region,
                                   forecast_date, method, configuration, lead_time)


async def get_analog_values(data_dir: str, region: str, forecast_date: str, method: str,
                            configuration: str, entity: int, lead_time: int | str):
    """
    Get the precipitation values for a given region, date, method, configuration,
    and entity.
    """
    return await asyncio.to_thread(_get_analog_values, data_dir, region, forecast_date,
                                   method, configuration, entity, lead_time)


async def get_analog_values_percentiles(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, lead_time: int | str, percentiles: list[int]):
    """
    Get the precipitation values for specific percentiles for a given region, date,
    method, configuration, and entity.
    """
    return await asyncio.to_thread(_get_analog_values_percentiles, data_dir, region,
                                   forecast_date, method, configuration, entity,
                                   lead_time, percentiles)


async def get_analog_values_best(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, lead_time: int | str, number: int):
    """
    Get the precipitation values for the best analogs for a given region, date, method,
    configuration, and entity.
    """
    return await asyncio.to_thread(_get_analog_values_best, data_dir, region,
                                   forecast_date, method, configuration, entity,
                                   lead_time, number)


async def get_entities_analog_values_percentile(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        lead_time: int | str, percentile: int, normalize: int = 10):
    """
    Get the precipitation values for a given region, date, method, configuration,
    target date, and percentile.
    """
    return await asyncio.to_thread(_get_entities_analog_values_percentile, data_dir,
                                   region, forecast_date, method, configuration,
                                   lead_time, percentile, normalize)


async def get_series_analog_values_best(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, number: int):
    """
    Get the time series of the best analog values for a given region, date, method,
    configuration, and entity.
    """
    return await asyncio.to_thread(_get_series_analog_values_best, data_dir, region,
                                   forecast_date, method, configuration, entity, number)


async def get_series_analog_values_percentiles(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, percentiles: list[int]):
    """
    Get the time series for specific percentiles for a given region, date, method,
    configuration, and entity.
    """
    return await asyncio.to_thread(_get_series_analog_values_percentiles, data_dir,
                                   region, forecast_date, method, configuration, entity,
                                   percentiles)


async def get_series_analog_values_percentiles_history(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, percentiles: list[int], number: int):
    """
    Get the time series for historical percentiles for a given region, date, method,
    configuration, entity, and number of past forecasts.
    """
    return await asyncio.to_thread(_get_series_analog_values_percentiles_history,
                                   data_dir, region, forecast_date, method,
                                   configuration, entity, percentiles, number)


def _get_reference_values(data_dir: str, region: str, forecast_date: str, method: str,
                          configuration: str, entity: int):
    """
    Synchronous function to get the reference values from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        axis = ds.reference_axis.values.tolist()
        values = ds.reference_values[entity_idx, :].astype(float).values.tolist()

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
        },
        "reference_axis": axis,
        "reference_values": values
    }


def _get_analogs(data_dir: str, region: str, forecast_date: str, method: str,
                 configuration: str, entity: int, lead_time: int | str):
    """
    Synchronous function to get the analogs from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            analogs = []
        else:
            start_idx, end_idx, target_date = row_indices
            analog_dates = [date.astype('datetime64[s]').item() for date in
                            ds.analog_dates.values[start_idx:end_idx]]
            analog_criteria = ds.analog_criteria[start_idx:end_idx].astype(
                float).values.tolist()
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values.tolist()
            ranks = list(range(1, len(analog_dates) + 1))
            analogs = [{"date": date, "criteria": criteria, "value": value, "rank": rank}
                       for date, criteria, value, rank in
                       zip(analog_dates, analog_criteria, values, ranks)]

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
        },
        "analogs": analogs
    }


def _get_analog_dates(data_dir: str, region: str, forecast_date: str, method: str,
                      configuration: str, lead_time: int | str):
    """
    Synchronous function to get the analog dates from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            analog_dates = []
        else:
            start_idx, end_idx, target_date = row_indices
            analog_dates = [date.astype('datetime64[s]').item() for date in
                            ds.analog_dates.values[start_idx:end_idx]]

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
        },
        "analog_dates": analog_dates
    }


def _get_analog_criteria(data_dir: str, region: str, forecast_date: str, method: str,
                         configuration: str, lead_time: int | str):
    """
    Synchronous function to get the analog criteria from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with (xr.open_dataset(file_path, engine="h5netcdf") as ds):
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            analog_criteria = []
        else:
            start_idx, end_idx, target_date = row_indices
            analog_criteria = ds.analog_criteria[start_idx:end_idx].astype(
                float).values.tolist()

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
        },
        "criteria": analog_criteria
    }


def _get_analog_values(data_dir: str, region: str, forecast_date: str, method: str,
                       configuration: str, entity: int, lead_time: int | str):
    """
    Synchronous function to get the precipitation values from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            values = []
        else:
            start_idx, end_idx, target_date = row_indices
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values.tolist()

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
        },
        "values": values
    }


def _get_analog_values_percentiles(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, lead_time: int | str, percentiles: list[int]):
    """
    Synchronous function to get the precipitation values for specific percentiles
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            values = [None for _ in percentiles]
        else:
            start_idx, end_idx, target_date = row_indices
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values
            values_sorted = np.sort(values)

            # Compute the percentiles
            frequencies = utils.build_cumulative_frequency(len(values))
            values = [float(np.interp(percentile / 100, frequencies, values_sorted)) for
                      percentile in percentiles]

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
            "percentiles": percentiles,
        },
        "percentiles": percentiles,
        "values": values
    }


def _get_analog_values_best(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, lead_time: int | str, number: int):
    """
    Synchronous function to get the precipitation values for the best analogs
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            values = []
        else:
            start_idx, end_idx, target_date = row_indices
            end_idx = min(end_idx, start_idx + number)
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
            "number": number
        },
        "values": values
    }


def _get_entities_analog_values_percentile(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        lead_time: int | str, percentile: int, normalize: int = 10):
    """
    Synchronous function to get the precipitation values for a specific percentile
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    target_date = utils.convert_to_target_date(forecast_date, lead_time)

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        station_ids = ds.station_ids.values.tolist()
        row_indices = utils.get_row_indices(ds, target_date)
        if row_indices is None:
            values = []
            values_normalized = []
        else:
            start_idx, end_idx, target_date = row_indices
            values = ds.analog_values_raw[:, start_idx:end_idx].astype(float).values
            values_sorted = np.sort(values, axis=1)

            # Compute the percentiles
            n_entities = values_sorted.shape[0]
            n_analogs = values_sorted.shape[1]
            freq = utils.build_cumulative_frequency(n_analogs)
            values = [float(np.interp(percentile / 100, freq, values_sorted[i, :])) for i in
                      range(n_entities)]

            # Get the reference values for normalization
            axis = ds.reference_axis.values.tolist()
            try:
                ref_idx = axis.index(normalize)
            except ValueError:
                raise ValueError(f"normalize must be in {axis}")
            ref_values = ds.reference_values[:, ref_idx].astype(float).values

            # Normalize the values
            values_normalized = np.array(values) / ref_values
            values_normalized = values_normalized.tolist()

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_date": target_date,
            "lead_time": utils.compute_lead_time(forecast_date, target_date),
            "method": method,
            "configuration": configuration,
            "percentile": percentile,
        },
        "entity_ids": station_ids,
        "values": values,
        "values_normalized": values_normalized,
    }


def _get_series_analog_values_best(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, number: int):
    """
    Synchronous function to get the time series of the best analog values
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        target_dates = [np.datetime64(date).astype('datetime64[s]').item() for date in
                        ds.target_dates.values]
        series_values = []
        series_dates = []
        entity_idx = utils.get_entity_index(ds, entity)
        analogs_nb = ds.analogs_nb.values
        for idx in range(len(analogs_nb)):
            start_idx = int(np.sum(analogs_nb[:idx]))
            end_idx = start_idx + min(number, int(analogs_nb[idx]))
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values.tolist()
            dates = [date.astype('datetime64[s]').item() for date in
                     ds.analog_dates.values[start_idx:end_idx]]
            series_values.append(values)
            series_dates.append(dates)

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
            "number": number
        },
        "target_dates": target_dates,
        "series_dates": series_dates,
        "series_values": series_values
    }


def _get_series_analog_values_percentiles(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, percentiles: list[int]):
    """
    Synchronous function to get the time series for specific percentiles
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path, engine="h5netcdf") as ds:
        entity_idx = utils.get_entity_index(ds, entity)
        analogs_nb = ds.analogs_nb.values
        series_values = np.ones((len(percentiles), len(analogs_nb))) * np.nan
        target_dates = [np.datetime64(date).astype('datetime64[s]').item() for date in
                        ds.target_dates.values]

        for analog_idx in range(len(analogs_nb)):
            start_idx = int(np.sum(analogs_nb[:analog_idx]))
            end_idx = start_idx + int(analogs_nb[analog_idx])
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values
            values_sorted = np.sort(values)

            # Compute the percentiles
            frequencies = utils.build_cumulative_frequency(analogs_nb[analog_idx])
            for i_pc, pc in enumerate(percentiles):
                val = np.interp(pc / 100, frequencies, values_sorted)
                series_values[i_pc, analog_idx] = val

    # Extract lists of values per percentile
    output = []
    for i_pc, pc in enumerate(percentiles):
        output.append(
            {"percentile": pc,
             "series_values": series_values[i_pc, :].tolist()})

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
            "percentiles": percentiles
        },
        "series_values": {
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "target_dates": target_dates,
            "series_percentiles": output
        }
    }


def _get_series_analog_values_percentiles_history(
        data_dir: str, region: str, forecast_date: str, method: str, configuration: str,
        entity: int, percentiles: list[int], number: int):
    """
    Synchronous function to get the time series for historical percentiles
    from the netCDF file.
    """
    if forecast_date == 'latest':
        forecast_date = utils.get_last_forecast_date(data_dir, region)

    region_path = utils.check_region_path(data_dir, region)
    diff = np.timedelta64(3, 'h')
    dt = utils.convert_to_datetime(forecast_date)
    counter_found = 0
    counter_tot = 0
    forecasts = []
    while True:
        if counter_found >= number:
            break
        if counter_tot > 50:
            break

        counter_tot += 1
        dt = dt - diff
        path_dir = f"{region_path}/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
        path = f"{path_dir}/{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}.{method}.{configuration}.nc"
        if not os.path.exists(path):
            continue

        dt_str = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}"
        series_percentiles = _get_series_analog_values_percentiles(
            data_dir, region, dt_str, method, configuration, entity, percentiles)
        series_percentiles = series_percentiles["series_values"]

        forecasts.append(series_percentiles)
        counter_found += 1

    return {
        "parameters": {
            "region": region,
            "forecast_date": utils.convert_to_datetime(forecast_date),
            "method": method,
            "configuration": configuration,
            "entity_id": entity,
            "percentiles": percentiles,
            "number": number
        },
        "past_forecasts": forecasts
    }
