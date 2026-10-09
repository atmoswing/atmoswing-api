import logging
from redis import asyncio as aioredis
from redis.exceptions import RedisError
import json
import hashlib
import functools
import os
import time

from atmoswing_api import config
from atmoswing_api.app.utils.logger import get_logger

logger = get_logger()
debug_mode = config.Settings().debug
logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Errors meaning that Redis cannot be used: Redis errors, network errors, and
# RuntimeError raised when a connection is used from another event loop than the
# one it was created in. They must never make a request fail.
REDIS_UNAVAILABLE_ERRORS = (RedisError, OSError, RuntimeError)


def _create_client():
    # The client connects lazily, so creating it does not need Redis to be reachable
    return aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


redis_client = _create_client()
# Assume available until a runtime error occurs; runtime operations will detect unavailability
redis_available = True
# When Redis becomes unavailable, set a retry timestamp instead of disabling forever
_redis_retry_at = 0.0
_redis_cooldown = 5.0  # seconds to wait before retrying


async def check_connection() -> bool:
    """
    Ping Redis and log whether caching is enabled. Must be called from the
    event loop serving the requests (e.g. at application startup).
    """
    try:
        await redis_client.ping()
        logger.info("Redis reachable at %s:%s; caching enabled", REDIS_HOST, REDIS_PORT)
        return True
    except REDIS_UNAVAILABLE_ERRORS as e:
        logger.warning("Redis unreachable at %s:%s; caching will be bypassed until "
                       "Redis is available: %s", REDIS_HOST, REDIS_PORT, e)
        return False


async def close():
    """
    Close the Redis connections (e.g. at application shutdown).
    """
    try:
        await redis_client.aclose()
    except REDIS_UNAVAILABLE_ERRORS as e:
        logger.debug("Error while closing the Redis client: %s", e)


def _mark_unavailable(operation: str, error: Exception):
    """
    Disable caching for the cooldown period. A client whose connections are bound
    to another event loop cannot recover, so it is replaced by a new one.
    """
    global redis_available, _redis_retry_at, redis_client
    redis_available = False
    _redis_retry_at = time.time() + _redis_cooldown
    if isinstance(error, RuntimeError):
        redis_client = _create_client()
    logger.warning("Redis error during %s; caching bypassed until %s: %s",
                   operation, _redis_retry_at, error)


def _make_cache_key(func, args, kwargs):
    """Create a stable cache key including module, function name, args and kwargs.
    Use json when possible, fall back to repr to handle non-serializable values.
    """
    try:
        key_payload = {
            "args": args,
            "kwargs": kwargs,
        }
        key_json = json.dumps(key_payload, default=str, sort_keys=True)
    except (TypeError, ValueError):
        key_json = repr((args, tuple(sorted(kwargs.items()))))

    key_data = f"{func.__module__}.{func.__name__}:{key_json}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def redis_cache(ttl=3600):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global redis_available

            # If Redis is currently marked unavailable, check whether it's time to retry.
            if not redis_available:
                if time.time() < _redis_retry_at:
                    return await func(*args, **kwargs)
                try:
                    await redis_client.ping()
                    redis_available = True
                    logger.info("Reconnected to Redis; caching re-enabled")
                except REDIS_UNAVAILABLE_ERRORS as e:
                    _mark_unavailable("PING", e)
                    return await func(*args, **kwargs)

            cache_key = _make_cache_key(func, args, kwargs)

            # Try to get the cached result; if Redis errors occur, schedule a retry and bypass caching
            try:
                cached = await redis_client.get(cache_key)
            except REDIS_UNAVAILABLE_ERRORS as e:
                _mark_unavailable("GET", e)
                return await func(*args, **kwargs)

            if cached is not None:
                try:
                    logger.debug("Cache hit for key %s", cache_key)
                    return json.loads(cached)
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Cache hit for key %s but failed to decode JSON", cache_key)
                    return cached
            else:
                logger.debug("Cache miss for key %s", cache_key)

            # Call the actual function
            result = await func(*args, **kwargs)

            # Attempt to cache the result; if serialization fails or Redis errors occur, skip caching and schedule retry
            try:
                payload = json.dumps(result, default=str)
            except (TypeError, ValueError):
                logger.warning("Result not JSON-serializable; skipping cache for key %s", cache_key)
                return result

            try:
                await redis_client.setex(cache_key, ttl, payload)
                logger.debug("Cache set for key %s", cache_key)
            except REDIS_UNAVAILABLE_ERRORS as e:
                _mark_unavailable("SETEX", e)

            return result

        return wrapper

    return decorator
