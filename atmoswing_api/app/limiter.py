import itertools
import logging
import math
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from limits import RateLimitItem, parse, storage, strategies
from starlette.types import ASGIApp, Receive, Scope, Send

from atmoswing_api.config import get_settings

# Rate limiting. Clients are identified by their IP address; behind a reverse proxy,
# uvicorn must trust its X-Forwarded-For header (FORWARDED_ALLOW_IPS environment
# variable), otherwise all clients share the proxy's address. The counters are kept
# in memory, so each worker process counts its own requests.

logger = logging.getLogger(__name__)

RATE_LIMIT_MESSAGE = "Rate limit exceeded. Please try again later."

_storage = storage.MemoryStorage()
_limiter = strategies.MovingWindowRateLimiter(_storage)

# Budget shared by all the requests of a client (settings.rate_limit)
application_limit: RateLimitItem = parse(get_settings().rate_limit)

_route_limit_ids = itertools.count()


def reset():
    """Forget all the counted requests."""
    _storage.reset()


def _client_key(scope: Scope) -> str:
    client = scope.get("client")
    return client[0] if client else "unknown"


def _hit(limit: RateLimitItem, namespace: str, key: str) -> int | None:
    """
    Count a request. Returns None when it is allowed, otherwise the number of
    seconds after which the client can retry.
    """
    if _limiter.hit(limit, namespace, key):
        return None
    logger.warning("Rate limit %s exceeded by %s (%s)", limit, key, namespace)
    reset_time = _limiter.get_window_stats(limit, namespace, key).reset_time
    return max(1, math.ceil(reset_time - time.time()))


class RateLimitMiddleware:
    """
    ASGI middleware applying application_limit to every HTTP request. It does not
    need to know the route, so it does not depend on how FastAPI stores routes.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            retry_after = _hit(application_limit, "application", _client_key(scope))
            if retry_after is not None:
                response = JSONResponse(status_code=429,
                                        content={"detail": RATE_LIMIT_MESSAGE},
                                        headers={"Retry-After": str(retry_after)})
                return await response(scope, receive, send)
        await self.app(scope, receive, send)


def route_limit(value: str):
    """
    FastAPI dependency adding a stricter limit to a route (on top of
    application_limit), e.g. dependencies=[Depends(route_limit("10/minute"))].
    """
    limit = parse(value)
    # Each dependency has its own counters, whatever the URL of the request
    namespace = f"route:{next(_route_limit_ids)}"

    async def check(request: Request):
        retry_after = _hit(limit, namespace, _client_key(request.scope))
        if retry_after is not None:
            raise HTTPException(status_code=429, detail=RATE_LIMIT_MESSAGE,
                                headers={"Retry-After": str(retry_after)})

    return check
