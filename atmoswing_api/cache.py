import logging
from redis import asyncio as aioredis
from redis.exceptions import RedisError
import json
import hashlib
import functools
import os

# Create an asyncio Redis client (don't await at import time)
redis_client = aioredis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)
# Assume available until a runtime error occurs; runtime operations will detect unavailability
redis_available = True


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
            global redis_available, redis_client

            # If Redis is unavailable, bypass caching
            if not redis_available:
                return await func(*args, **kwargs)

            cache_key = _make_cache_key(func, args, kwargs)

            # Try to get the cached result; if Redis errors occur, disable caching at runtime
            try:
                cached = await redis_client.get(cache_key)
            except RedisError:
                logging.exception("Redis error during GET; disabling cache")
                redis_available = False
                return await func(*args, **kwargs)

            if cached is not None:
                try:
                    return json.loads(cached)
                except (json.JSONDecodeError, TypeError):
                    # If value isn't JSON, return raw cached value
                    return cached

            # Call the actual function
            result = await func(*args, **kwargs)

            # Attempt to cache the result; if serialization fails or Redis errors occur, skip caching
            try:
                payload = json.dumps(result, default=str)
                await redis_client.setex(cache_key, ttl, payload)
            except (TypeError, ValueError):
                logging.debug("Result not JSON-serializable; skipping cache for key %s", cache_key)
            except RedisError:
                logging.exception("Redis error during SETEX; disabling cache")
                redis_available = False

            return result

        return wrapper
    return decorator
