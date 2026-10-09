import asyncio
import functools
import logging
import time
from fastapi import HTTPException

from atmoswing_api import config
from atmoswing_api.app.utils import utils
from atmoswing_api.app.utils.errors import InvalidInputError, DataNotFoundError

# Duration (in seconds) during which a resolved 'latest' forecast date is reused
# before the region directory is scanned again.
LATEST_FORECAST_DATE_TTL = 10.0

_latest_forecast_dates: dict[tuple[str, str], tuple[float, str]] = {}


def _to_http_exception(e: Exception, context: str) -> HTTPException:
    """
    Translate an exception into an HTTP error. Only messages of InvalidInputError
    and DataNotFoundError are returned to the client; other errors are logged and
    returned as a generic message, so that no server paths or internal details
    are exposed.
    """
    if isinstance(e, InvalidInputError):
        logging.info(f"Invalid request ({context}): {e}")
        return HTTPException(status_code=400, detail=f"Invalid request ({e})")
    if isinstance(e, DataNotFoundError):
        logging.info(f"Data not found ({context}): {e}")
        return HTTPException(status_code=400, detail=f"Region or forecast not found ({e})")
    if isinstance(e, FileNotFoundError):
        logging.error(f"File not found ({context})", exc_info=e)
        return HTTPException(status_code=400, detail="Region or forecast not found")
    logging.error(f"Unexpected error ({context})", exc_info=e)
    return HTTPException(status_code=500, detail="Internal server error.")


async def handle_request(func, settings: config.Settings, region: str, **kwargs):
    """
    Call a service function and translate its exceptions into HTTP errors.
    """
    try:
        result = await func(settings.data_dir, region, **kwargs)
    except Exception as e:
        raise _to_http_exception(e, f"{func.__name__}, region {region}, {kwargs}")

    if result is None:
        logging.error(f"{func.__name__} returned None for region {region} ({kwargs})")
        raise HTTPException(status_code=500, detail="Internal server error.")

    return result


async def resolve_forecast_date(data_dir: str, region: str, forecast_date: str) -> str:
    """
    Convert a forecast date to its canonical form "YYYY-MM-DDTHH". The value
    'latest' is replaced by the last available forecast date of the region,
    which is reused for LATEST_FORECAST_DATE_TTL seconds.
    """
    if forecast_date != 'latest':
        return f"{utils.convert_to_datetime(forecast_date):%Y-%m-%dT%H}"

    key = (data_dir, region)
    now = time.monotonic()
    cached = _latest_forecast_dates.get(key)
    if cached is not None and now - cached[0] < LATEST_FORECAST_DATE_TTL:
        return cached[1]

    resolved = await asyncio.to_thread(utils.get_last_forecast_date, data_dir, region)
    _latest_forecast_dates[key] = (now, resolved)

    return resolved


def resolve_latest(func):
    """
    Route decorator replacing the 'forecast_date' argument by its canonical form
    (see resolve_forecast_date) before calling the route. It must be placed
    between @router.get and @redis_cache, so that both the Redis cache and the
    prebuilt cache are looked up with the actual forecast date, never 'latest'.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        region = kwargs["region"]
        try:
            kwargs["forecast_date"] = await resolve_forecast_date(
                kwargs["settings"].data_dir, region, kwargs["forecast_date"])
        except Exception as e:
            raise _to_http_exception(e, f"resolving forecast date, region {region}")
        return await func(*args, **kwargs)

    return wrapper
