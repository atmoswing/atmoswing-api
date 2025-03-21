import os

import xarray as xr
import numpy as np
import asyncio

from ..utils import utils


async def get_reference_values(data_dir: str, region: str, forecast_date: str,
                               method: str, configuration: str, entity: int):
    """
    Get the reference values (e.g. for different return periods) for a given region,
    forecast date, method, configuration, and entity.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_reference_values, region_path, forecast_date,
                                   method, configuration, entity)


async def get_analogs(data_dir: str, region: str, forecast_date: str, method: str,
                      configuration: str, entity: int, target_date: str):
    """
    Get the analogs for a given region, forecast date, method, configuration, entity,
    and target date.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_analogs, region_path, forecast_date, method,
                                   configuration, entity, target_date)


async def get_analog_dates(data_dir: str, region: str, forecast_date: str, method: str,
                           configuration: str, target_date: str):
    """
    Get the analog dates for a given region, date, method, configuration,
    and target date.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_analog_dates, region_path, forecast_date,
                                   method, configuration, target_date)


async def get_analog_criteria(data_dir: str, region: str, forecast_date: str,
                              method: str, configuration: str, target_date: str):
    """
    Get the analog criteria for a given region, date, method, configuration,
    and target date.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_analog_criteria, region_path, forecast_date,
                                   method, configuration, target_date)


async def get_analog_values(data_dir: str, region: str, forecast_date: str, method: str,
                            configuration: str, entity: int, target_date: str):
    """
    Get the precipitation values for a given region, date, method, configuration,
    and entity.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_analog_values, region_path, forecast_date,
                                   method, configuration, entity, target_date)


async def get_series_analog_values_best(data_dir: str, region: str, forecast_date: str,
                                        method: str, configuration: str, entity: int,
                                        number: int):
    """
    Get the time series of the best analog values for a given region, date, method,
    configuration, and entity.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_series_analog_values_best, region_path,
                                   forecast_date, method, configuration, entity, number)


async def get_series_analog_values_percentiles(data_dir: str, region: str,
                                               forecast_date: str, method: str,
                                               configuration: str, entity: int,
                                               percentiles: list[int]):
    """
    Get the time series for specific percentiles for a given region, date, method,
    configuration, and entity.
    """
    region_path = utils.check_region_path(data_dir, region)
    return await asyncio.to_thread(_get_series_analog_values_percentiles, region_path,
                                   forecast_date, method, configuration, entity,
                                   percentiles)


def _get_reference_values(region_path: str, forecast_date: str, method: str,
                          configuration: str, entity: int):
    """
    Synchronous function to get the reference values from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        entity_idx = _get_entity_index(ds, entity)
        axis = ds.reference_axis.values.tolist()
        values = ds.reference_values[entity_idx,:].astype(float).values.tolist()

    reference_values = {"axis": axis, "values": values}

    return {"reference_values": reference_values}


def _get_analogs(region_path: str, forecast_date: str, method: str, configuration: str,
                 entity: int, target_date: str):
    """
    Synchronous function to get the analogs from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        entity_idx = _get_entity_index(ds, entity)
        start_idx, end_idx = _get_row_indices(ds, target_date)
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

    return {"analogs": analogs}


def _get_analog_dates(region_path: str, forecast_date: str, method: str,
                      configuration: str, target_date: str):
    """
    Synchronous function to get the analog dates from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        start_idx, end_idx = _get_row_indices(ds, target_date)
        analog_dates = [date.astype('datetime64[s]').item() for date in
                        ds.analog_dates.values[start_idx:end_idx]]

    return {"dates": analog_dates}


def _get_analog_criteria(region_path: str, forecast_date: str, method: str,
                         configuration: str, target_date: str):
    """
    Synchronous function to get the analog criteria from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with (xr.open_dataset(file_path) as ds):
        start_idx, end_idx = _get_row_indices(ds, target_date)
        analog_criteria = ds.analog_criteria[start_idx:end_idx].astype(
            float).values.tolist()

    return {"criteria": analog_criteria}


def _get_analog_values(region_path: str, forecast_date: str, method: str,
                       configuration: str, entity: int, target_date: str):
    """
    Synchronous function to get the precipitation values from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        entity_idx = _get_entity_index(ds, entity)
        start_idx, end_idx = _get_row_indices(ds, target_date)
        values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
            float).values.tolist()

    return {"values": values}


def _get_series_analog_values_best(region_path: str, forecast_date: str, method: str,
                                   configuration: str, entity: int, number: int):
    """
    Synchronous function to get the time series of the best analog values
    from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        series_values = []
        entity_idx = _get_entity_index(ds, entity)
        analogs_nb = ds.analogs_nb.values
        for idx in range(len(analogs_nb)):
            start_idx = int(np.sum(analogs_nb[:idx]))
            end_idx = start_idx + min(number, int(analogs_nb[idx]))
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values.tolist()
            series_values.append(values)

    return {"series_values": series_values}


def _get_series_analog_values_percentiles(region_path: str, forecast_date: str,
                                          method: str, configuration: str, entity: int,
                                          percentiles: list[int]):
    """
    Synchronous function to get the time series for specific percentiles
    from the netCDF file.
    """
    file_path = utils.get_file_path(region_path, forecast_date, method, configuration)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with xr.open_dataset(file_path) as ds:
        entity_idx = _get_entity_index(ds, entity)
        analogs_nb = ds.analogs_nb.values
        series_values = np.zeros((len(percentiles), len(analogs_nb)))
        for analog_idx in range(len(analogs_nb)):
            start_idx = int(np.sum(analogs_nb[:analog_idx]))
            end_idx = start_idx + int(analogs_nb[analog_idx])
            values = ds.analog_values_raw[entity_idx, start_idx:end_idx].astype(
                float).values
            values_sorted = np.sort(values).flatten()

            # Compute the percentiles with numpy
            # series_values[:, analog_idx] = np.percentile(values, percentiles)

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

    return {"series_percentiles": output}


def _get_row_indices(ds, target_date):
    # Get the start and end indices for the entity
    target_date_idx = _get_target_date_index(ds, target_date)
    analogs_nb = ds.analogs_nb.values
    start_idx = int(np.sum(analogs_nb[:target_date_idx]))
    end_idx = start_idx + int(analogs_nb[target_date_idx])
    return start_idx, end_idx


def _get_target_date_index(ds, target_date):
    # Find the lead time
    target_dates = ds.target_dates.values
    target_date = utils.convert_to_datetime(target_date)
    target_date_idx = -1
    for i, date in enumerate(target_dates):
        date = np.datetime64(date).astype('datetime64[s]').item()
        if date == target_date:
            target_date_idx = i
            break
    return target_date_idx


def _get_entity_index(ds, entity):
    # Find the entity ID
    station_ids = ds.station_ids.values
    indices = np.where(station_ids == entity)[0]
    entity_idx = int(indices[0]) if indices.size > 0 else -1
    if entity_idx == -1:
        raise ValueError(f"Entity not found: {entity}")
    return entity_idx
