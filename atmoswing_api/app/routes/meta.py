from typing import Annotated
from fastapi import APIRouter, Depends

from atmoswing_api.config import Settings, get_settings
from atmoswing_api.cache import redis_cache
from atmoswing_api.app.routes.common import handle_request, resolve_latest
from atmoswing_api.app.models.models import (
    EntitiesListResponse, MethodConfigsListResponse, MethodsListResponse)
from atmoswing_api.app.services.meta import (
    get_config_data, get_entities_list, get_last_forecast_date,
    get_method_configs_list, get_method_list, get_relevant_entities_list,
    has_forecast_date)
from atmoswing_api.app.utils.utils import load_prebuilt_result, sanitize_unicode_surrogates

router = APIRouter()


@router.get("/show-config",
            summary="Show config")
async def show_config(
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Show the current configuration settings.
    """
    return await get_config_data(settings.data_dir)


@router.get("/{region}/last-forecast-date",
            summary="Last available forecast date")
async def last_forecast_date(
        region: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Get the last available forecast date for a given region.
    """
    return await handle_request(get_last_forecast_date, settings, region)


@router.get("/{region}/{forecast_date}/has-forecasts",
            summary="Check if forecasts are available")
@resolve_latest
@redis_cache(ttl=120)
async def has_forecasts(
        region: str,
        forecast_date: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Check if forecasts are available for a given region and forecast date.
    """
    return await handle_request(has_forecast_date, settings, region,
                                 forecast_date=forecast_date)


@router.get("/{region}/{forecast_date}/methods",
            summary="List of available methods",
            response_model=MethodsListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def list_methods(
        region: str,
        forecast_date: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Get the list of available methods for a given region.
    """
    prebuilt = load_prebuilt_result(settings.data_dir, 'list_methods', region, forecast_date)
    if prebuilt is not None:
        return sanitize_unicode_surrogates(prebuilt)
    result = await handle_request(get_method_list, settings, region,
                                   forecast_date=forecast_date)
    return sanitize_unicode_surrogates(result)


@router.get("/{region}/{forecast_date}/methods-and-configs",
            summary="List of available methods and configurations",
            response_model=MethodConfigsListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def list_methods_and_configs(
        region: str,
        forecast_date: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Get the list of available methods and configs for a given region.
    """
    prebuilt = load_prebuilt_result(settings.data_dir, 'list_methods_and_configs', region, forecast_date)
    if prebuilt is not None:
        return sanitize_unicode_surrogates(prebuilt)
    result = await handle_request(get_method_configs_list, settings, region,
                                   forecast_date=forecast_date)
    return sanitize_unicode_surrogates(result)


@router.get("/{region}/{forecast_date}/{method}/{configuration}/entities",
            summary="List of available entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def list_entities(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Get the list of available entities for a given region, forecast_date, method, and configuration.
    """
    return await handle_request(get_entities_list, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration)


@router.get("/{region}/{forecast_date}/{method}/{configuration}/relevant-entities",
            summary="List of relevant entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
@resolve_latest
@redis_cache(ttl=3600)
async def list_relevant_entities(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        settings: Annotated[Settings, Depends(get_settings)]):
    """
    Get the list of relevant entities for a given region, forecast_date, method, and configuration.
    """
    return await handle_request(get_relevant_entities_list, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration)
