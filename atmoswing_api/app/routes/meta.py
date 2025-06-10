import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated
from typing import List

from atmoswing_api import config
from atmoswing_api.cache import *
from atmoswing_api.app.services.meta import get_last_forecast_date, \
    get_method_list, get_method_configs_list, get_entities_list, get_config_data, \
    get_relevant_entities_list
from atmoswing_api.app.models.models import *

router = APIRouter()


@lru_cache
def get_settings():
    return config.Settings()


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


@redis_cache(ttl=3600)
@router.get("/{region}/{forecast_date}/methods",
            summary="List of available methods",
            response_model=MethodsListResponse,
            response_model_exclude_none=True)
async def list_methods(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods for a given region.
    """
    return await _handle_request(get_method_list, settings, region,
                                 forecast_date=forecast_date)


@redis_cache(ttl=3600)
@router.get("/{region}/{forecast_date}/methods-and-configs",
            summary="List of available methods and configurations",
            response_model=MethodConfigsListResponse,
            response_model_exclude_none=True)
async def list_methods_and_configs(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods and configs for a given region.
    """
    return await _handle_request(get_method_configs_list, settings, region,
                                 forecast_date=forecast_date)


@redis_cache(ttl=3600)
@router.get("/{region}/{forecast_date}/{method}/{configuration}/entities",
            summary="List of available entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
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


@redis_cache(ttl=3600)
@router.get("/{region}/{forecast_date}/{method}/{configuration}/relevant-entities",
            summary="List of available entities",
            response_model=EntitiesListResponse,
            response_model_exclude_none=True)
async def list_entities(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available entities for a given region, forecast_date, method, and configuration.
    """
    return await _handle_request(get_relevant_entities_list, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration)
