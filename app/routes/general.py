import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated

from .. import config
from app.services.general import get_model_list, get_last_forecast_date_from_files

router = APIRouter()


@lru_cache
def get_settings():
    return config.Settings()


@router.get("/{region}/models", summary="List of available models")
async def list_models(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available models for a given region.
    """
    return await _handle_request(region, settings, get_model_list)


@router.get("/{region}/last-forecast-date", summary="Last available forecast date")
async def get_last_forecast_date(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the last available forecast date for a given region.
    """
    return await _handle_request(region, settings, get_last_forecast_date_from_files)


# Helper function to handle requests and catch exceptions
async def _handle_request(region: str, settings: config.Settings, func):
    try:
        return await func(region, settings.data_dir)
    except FileNotFoundError:
        logging.error(f"Files not found for region: {region}")
        raise HTTPException(status_code=404, detail="Region or forecast not found")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
