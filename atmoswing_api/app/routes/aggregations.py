from typing import Annotated
from fastapi import APIRouter, Depends, Query

from atmoswing_api.config import Settings, get_settings
from atmoswing_api.cache import redis_cache
from atmoswing_api.app.routes.common import handle_request, resolve_latest
from atmoswing_api.app.models.models import (
    EntitiesValuesPercentileAggregationResponse,
    SeriesSynthesisPerMethodListResponse, SeriesSynthesisTotalListResponse)
from atmoswing_api.app.services.aggregations import (
    get_entities_analog_values_percentile, get_series_synthesis_per_method,
    get_series_synthesis_total)
from atmoswing_api.app.utils.utils import load_prebuilt_result

router = APIRouter()


@router.get("/{region}/{forecast_date}/{method}/{lead_time}/entities-values-percentile/{percentile}",
            summary="Analog values for a given region, forecast_date, method, "
                    "lead time, and percentile, aggregated by selecting the "
                    "relevant configuration per entity",
            response_model=EntitiesValuesPercentileAggregationResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def entities_analog_values_percentile(
        region: str,
        forecast_date: str,
        method: str,
        lead_time: int|str,
        percentile: int,
        settings: Annotated[Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the analog dates for a given region, forecast_date, method, configuration, and lead_time.
    """
    prebuilt = load_prebuilt_result(settings.data_dir, 'entities_analog_values_percentile', region, forecast_date, percentile, normalize, method=method, lead_time=lead_time)
    if prebuilt is not None:
        return prebuilt
    return await handle_request(get_entities_analog_values_percentile, settings,
                                 region, forecast_date=forecast_date, method=method,
                                 lead_time=lead_time, percentile=percentile,
                                 normalize=normalize)


@router.get("/{region}/{forecast_date}/series-synthesis-per-method/{percentile}",
            summary="Largest values for a given region, forecast_date, method, "
                    "and percentile, aggregated by selecting the largest values for "
                    "the relevant configurations per entity",
            response_model=SeriesSynthesisPerMethodListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def series_synthesis_per_method(
        region: str,
        forecast_date: str,
        percentile: int,
        settings: Annotated[Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the largest analog values for a given region, forecast_date, and percentile.
    """
    prebuilt = load_prebuilt_result(settings.data_dir, 'series_synthesis_per_method', region, forecast_date, percentile, normalize)
    if prebuilt is not None:
        return prebuilt
    return await handle_request(get_series_synthesis_per_method, settings,
                                 region, forecast_date=forecast_date,
                                 percentile=percentile, normalize=normalize)


@router.get("/{region}/{forecast_date}/series-synthesis-total/{percentile}",
            summary="Largest values for a given region, forecast_date, "
                    "and percentile, aggregated by time steps",
            response_model=SeriesSynthesisTotalListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def series_synthesis_total(
        region: str,
        forecast_date: str,
        percentile: int,
        settings: Annotated[Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the largest analog values for a given region, forecast_date, and percentile.
    """
    prebuilt = load_prebuilt_result(settings.data_dir, 'series_synthesis_total', region, forecast_date, percentile, normalize)
    if prebuilt is not None:
        return prebuilt
    return await handle_request(get_series_synthesis_total, settings,
                                 region, forecast_date=forecast_date,
                                 percentile=percentile, normalize=normalize)
