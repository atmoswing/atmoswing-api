import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated
from typing import List

import config
from app.services.meta import get_last_forecast_date_from_files, \
    get_method_list, get_method_configs_list, get_entities_list
from app.models.meta import Entity, Method, MethodConfig

router = APIRouter()


@lru_cache
def get_settings():
    return config.Settings()


# Helper function to handle requests and catch exceptions
async def _handle_request(func, settings: config.Settings, region: str, **kwargs):
    try:
        return await func(settings.data_dir, region, **kwargs)
    except FileNotFoundError:
        logging.error(f"Files not found for region: {region}")
        raise HTTPException(status_code=404, detail="Region or forecast not found")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{region}/last-forecast-date",
            summary="Last available forecast date")
async def get_last_forecast_date(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the last available forecast date for a given region.
    """
    return await _handle_request(get_last_forecast_date_from_files, settings, region)


@router.get("/{region}/{forecast_date}/methods",
            summary="List of available methods",
            response_model=List[Method])
async def list_methods(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods for a given region.
    """
    return await _handle_request(get_method_list, settings, region,
                                 forecast_date=forecast_date)


@router.get("/{region}/{forecast_date}/methods-and-configs",
            summary="List of available methods and configurations",
            response_model=List[MethodConfig])
async def list_methods_and_configs(
        region: str,
        forecast_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available methods and configs for a given region.
    """
    return await _handle_request(get_method_configs_list, settings, region,
                                 forecast_date=forecast_date)


@router.get("/{region}/{forecast_date}/{method}/{configuration}/entities",
            summary="List of available entities",
            response_model=List[Entity])
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
