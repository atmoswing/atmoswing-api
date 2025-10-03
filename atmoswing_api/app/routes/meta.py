import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated
from typing import List

from atmoswing_api import config
from atmoswing_api.cache import *
from atmoswing_api.app.services.meta import get_last_forecast_date, \
    get_method_list, get_method_configs_list, get_entities_list, get_config_data, \
    get_relevant_entities_list, has_forecast_date
from atmoswing_api.app.models.models import *
from atmoswing_api.app.utils.utils import sanitize_unicode_surrogates, compute_cache_hash, make_cache_paths
import json
from pathlib import Path

router = APIRouter()


@lru_cache
def get_settings():
    return config.Settings()


# Helper to load prebuilt cache if available
def load_prebuilt_result(settings: config.Settings, func_name: str, region: str, forecast_date: str):
    prebuilt_dir = Path(settings.data_dir) / '.prebuilt_cache'
    if not prebuilt_dir.exists():
        return None
    hash_suffix = compute_cache_hash(func_name, region, forecast_date)
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
        return await func(settings.data_dir, region, **kwargs)
    except FileNotFoundError as e:
        logging.error(f"Files not found for region: {region} "
                      f"(directory: {settings.data_dir})")
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=400, detail=f"Region or forecast not found ({e})")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error ({e})")


@router.get("/show-config",
            summary="Show config")
async def show_config(
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Show the current configuration settings.
    """
    return await get_config_data(settings.data_dir)


@redis_cache(ttl=120)
@router.get("/{region}/last-forecast-date",
            summary="Last available forecast date")
async def last_forecast_date(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the last available forecast date for a given region.
    """
    return await _handle_request(get_last_forecast_date, settings, region)


@router.get("/{region}/{forecast_date}/has-forecasts",
            summary="Check if forecasts are available")
@redis_cache(ttl=120)
async def has_forecasts(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Check if forecasts are available for a given region and forecast date.
    """
    return await _handle_request(has_forecast_date, settings, region,
                                 forecast_date=forecast_date)


@router.get("/{region}/{forecast_date}/methods",
            summary="List of available methods",
            response_model=MethodsListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def list_methods(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods for a given region.
    """
    prebuilt = load_prebuilt_result(settings, 'list_methods', region, forecast_date)
    if prebuilt is not None:
        return sanitize_unicode_surrogates(prebuilt)
    result = await _handle_request(get_method_list, settings, region,
                                   forecast_date=forecast_date)
    return sanitize_unicode_surrogates(result)


@router.get("/{region}/{forecast_date}/methods-and-configs",
            summary="List of available methods and configurations",
            response_model=MethodConfigsListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def list_methods_and_configs(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods and configs for a given region.
    """
    prebuilt = load_prebuilt_result(settings, 'list_methods_and_configs', region, forecast_date)
    if prebuilt is not None:
        return sanitize_unicode_surrogates(prebuilt)
    result = await _handle_request(get_method_configs_list, settings, region,
                                   forecast_date=forecast_date)
    return sanitize_unicode_surrogates(result)


@router.get("/{region}/{forecast_date}/{method}/{configuration}/entities",
            summary="List of available entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def list_entities(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available entities for a given region, forecast_date, method, and configuration.
    """
    return await _handle_request(get_entities_list, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration)


@router.get("/{region}/{forecast_date}/{method}/{configuration}/relevant-entities",
            summary="List of relevant entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
@redis_cache(ttl=3600)
async def list_relevant_entities(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of relevant entities for a given region, forecast_date, method, and configuration.
    """
    return await _handle_request(get_relevant_entities_list, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration)
