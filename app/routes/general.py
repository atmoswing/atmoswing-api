from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated

from .. import config
from ..main import get_settings
from app.services.general import get_model_list, get_last_forecast_date

router = APIRouter()


@router.get("/{region}/models", summary="List of available models")
async def list_models(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the list of available models for a given region.
    """
    try:
        return await get_model_list(region, settings.data_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Region or forecast not found")


@router.get("/{region}/last-forecast-date", summary="Last available forecast date")
async def get_last_forecast_date(
        region: str,
        settings: Annotated[config.Settings, Depends(get_settings)]):
    """
    Get the last available forecast date for a given region.
    """
    try:
        return await get_last_forecast_date(region, settings.data_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Region or forecast not found")
