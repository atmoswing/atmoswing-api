import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated

import config
from app.models.forecast import AnalogValues
from app.services.forecasts import get_analog_values

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


@router.get("/{region}/{forecast_date}/{method}/{configuration}/{entity}/{target_date}",
            summary="Analog values for a given entity",
            response_model=AnalogValues)
async def analog_values(
        region: str,
        forecast_date: str,
        method: str,
        configuration: str,
        entity: int,
        target_date: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the precipitation values for a given region, forecast_date, method, configuration, entity, target_date.
    """
    return await _handle_request(get_analog_values, settings, region,
                                 forecast_date=forecast_date, method=method,
                                 configuration=configuration, entity=entity,
                                 target_date=target_date)
