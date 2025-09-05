import logging
from redis import asyncio as aioredis
from redis.exceptions import RedisError
import asyncio
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

# Create an asyncio Redis client (don't await at import time)
redis_client = aioredis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)
# Assume available until a runtime error occurs; runtime operations will detect unavailability
redis_available = True
# When Redis becomes unavailable, set a retry timestamp instead of disabling forever
_redis_retry_at = 0.0
_redis_cooldown = 5.0  # seconds to wait before retrying

# Log Redis connection at startup
try:
    asyncio.get_event_loop().run_until_complete(redis_client.ping())
    logger.info(f"Redis reachable at {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}; caching enabled")
except Exception as e:
    logger.warning(f"Redis not reachable at startup: {e}")

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
            global redis_available, _redis_retry_at

            # If Redis is currently marked unavailable, check whether it's time to retry.
            now = time.time()
            if not redis_available:
                if now >= _redis_retry_at:
                    try:
                        await redis_client.ping()
                        redis_available = True
                        logger.info("Reconnected to Redis; caching re-enabled")
                    except RedisError:
                        _redis_retry_at = now + _redis_cooldown
                        logger.debug("Redis still unavailable; next retry at %s", _redis_retry_at)
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)

            cache_key = _make_cache_key(func, args, kwargs)

            # Try to get the cached result; if Redis errors occur, schedule a retry and bypass caching
            try:
                cached = await redis_client.get(cache_key)
            except RedisError:
                now = time.time()
                _redis_retry_at = now + _redis_cooldown
                redis_available = False
                logger.exception("Redis error during GET; will retry after %s", _redis_retry_at)
                logger.debug("Cache failed for key %s due to Redis error", cache_key)
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
                await redis_client.setex(cache_key, ttl, payload)
                logger.debug("Cache set for key %s", cache_key)
            except (TypeError, ValueError):
                logger.debug("Result not JSON-serializable; skipping cache for key %s", cache_key)
                logger.warning("Cache failed for key %s due to serialization error", cache_key)
            except RedisError:
                now = time.time()
                _redis_retry_at = now + _redis_cooldown
                redis_available = False
                logger.exception("Redis error during SETEX; will retry after %s", _redis_retry_at)
                logger.debug("Cache failed for key %s due to Redis error", cache_key)

            return result

        return wrapper

    return decorator
