import logging
from fastapi import HTTPException

from atmoswing_api import config
from atmoswing_api.app.utils.errors import InvalidInputError, DataNotFoundError


async def handle_request(func, settings: config.Settings, region: str, **kwargs):
    """
    Call a service function and translate its exceptions into HTTP errors.
    Only messages of InvalidInputError and DataNotFoundError are returned to the
    client; other errors are logged and returned as a generic message, so that
    no server paths or internal details are exposed.
    """
    try:
        result = await func(settings.data_dir, region, **kwargs)
    except InvalidInputError as e:
        logging.info(f"Invalid request for region {region} ({kwargs}): {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request ({e})")
    except DataNotFoundError as e:
        logging.info(f"Data not found for region {region} ({kwargs}): {e}")
        raise HTTPException(status_code=400, detail=f"Region or forecast not found ({e})")
    except FileNotFoundError:
        logging.exception(f"File not found for region {region} ({kwargs})")
        raise HTTPException(status_code=400, detail="Region or forecast not found")
    except Exception:
        logging.exception(f"Unexpected error in {func.__name__} for region "
                          f"{region} ({kwargs})")
        raise HTTPException(status_code=500, detail="Internal server error.")

    if result is None:
        logging.error(f"{func.__name__} returned None for region {region} ({kwargs})")
        raise HTTPException(status_code=500, detail="Internal server error.")

    return result
