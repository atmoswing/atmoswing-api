import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, Query

from atmoswing_api import config
from atmoswing_api.cache import *
from atmoswing_api.app.models.models import *
from atmoswing_api.app.services.aggregations import *
from atmoswing_api.app.utils.utils import compute_cache_hash, make_cache_paths
import json
from pathlib import Path

router = APIRouter()
debug = False


@lru_cache
def get_settings():
    return config.Settings()


# Helper function to check for a prebuilt JSON and return it if present
def load_prebuilt_result(settings: config.Settings, func_name: str, region: str, forecast_date: str, percentile: int | None = None, normalize: int | None = None, **extra):
    prebuilt_dir = Path(settings.data_dir) / '.prebuilt_cache'
    if not prebuilt_dir.exists():
        return None
    hash_suffix = compute_cache_hash(func_name, region, forecast_date, percentile, normalize, **extra)
    cache_path = make_cache_paths(prebuilt_dir, func_name, region, forecast_date, hash_suffix)
    pattern = cache_path.name
    candidates = sorted(prebuilt_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    try:
        data = json.loads(candidates[0].read_text(encoding='utf-8'))
        return data.get('result')
    except Exception as e:
        logging.warning(f"Failed to read prebuilt cache {candidates[0]}: {e}")
        return None


# Helper function to handle requests and catch exceptions
async def _handle_request(func, settings: config.Settings, region: str, **kwargs):
    try:
        result = await func(settings.data_dir, region, **kwargs)
        if debug:
            logging.info(f"Result from {func.__name__}: {result}")
        if result is None:
            raise ValueError("The result is None")
        return result
    except FileNotFoundError as e:
        logging.error(f"Files not found for region: {region} "
                      f"(directory: {settings.data_dir})")
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=400, detail=f"Region or forecast not found ({e})")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error ({e})")


@router.get("/{region}/{forecast_date}/{method}/{lead_time}/entities-values-percentile/{percentile}",
            summary="Analog values for a given region, forecast_date, method, "
                    "lead time, and percentile, aggregated by selecting the "
                    "relevant configuration per entity",
            response_model=EntitiesValuesPercentileAggregationResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def entities_analog_values_percentile(
        region: str,
        forecast_date: str,
        method: str,
        lead_time: int|str,
        percentile: int,
        settings: Annotated[config.Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the analog dates for a given region, forecast_date, method, configuration, and lead_time.
    """
    prebuilt = load_prebuilt_result(settings, 'entities_analog_values_percentile', region, forecast_date, percentile, normalize, method=method, lead_time=lead_time)
    if prebuilt is not None:
        return prebuilt
    return await _handle_request(get_entities_analog_values_percentile, settings,
                                 region, forecast_date=forecast_date, method=method,
                                 lead_time=lead_time, percentile=percentile,
                                 normalize=normalize)


@router.get("/{region}/{forecast_date}/series-synthesis-per-method/{percentile}",
            summary="Largest values for a given region, forecast_date, method, "
                    "and percentile, aggregated by selecting the largest values for "
                    "the relevant configurations per entity",
            response_model=SeriesSynthesisPerMethodListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def series_synthesis_per_method(
        region: str,
        forecast_date: str,
        percentile: int,
        settings: Annotated[config.Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the largest analog values for a given region, forecast_date, and percentile.
    """
    prebuilt = load_prebuilt_result(settings, 'series_synthesis_per_method', region, forecast_date, percentile, normalize)
    if prebuilt is not None:
        return prebuilt
    return await _handle_request(get_series_synthesis_per_method, settings,
                                 region, forecast_date=forecast_date,
                                 percentile=percentile, normalize=normalize)


@router.get("/{region}/{forecast_date}/series-synthesis-total/{percentile}",
            summary="Largest values for a given region, forecast_date, "
                    "and percentile, aggregated by time steps",
            response_model=SeriesSynthesisTotalListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def series_synthesis_total(
        region: str,
        forecast_date: str,
        percentile: int,
        settings: Annotated[config.Settings, Depends(get_settings)],
        normalize: int = Query(10)):
    """
    Get the largest analog values for a given region, forecast_date, and percentile.
    """
    prebuilt = load_prebuilt_result(settings, 'series_synthesis_total', region, forecast_date, percentile, normalize)
    if prebuilt is not None:
        return prebuilt
    return await _handle_request(get_series_synthesis_total, settings,
                                 region, forecast_date=forecast_date,
                                 percentile=percentile, normalize=normalize)
