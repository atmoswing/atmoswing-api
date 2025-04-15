import logging
import redis
import json
import hashlib
import functools
import os

# Try to connect to Redis
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )
    redis_client.ping()  # Test connection
    redis_available = True
except (redis.ConnectionError, redis.TimeoutError):
    logging.exception("Redis is not available")
    redis_client = None
    redis_available = False

def redis_cache(ttl=3600):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis is unavailable, bypass caching
            if not redis_available:
                return await func(*args, **kwargs)

            # Create a unique cache key based on the function and arguments
            key_data = f"{func.__name__}:{json.dumps(kwargs, sort_keys=True)}"
            cache_key = hashlib.sha256(key_data.encode()).hexdigest()

            # Try to get the cached result
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call the actual function
            result = await func(*args, **kwargs)

            # Cache the result
            await redis_client.setex(cache_key, ttl, json.dumps(result))
            return result

        return wrapper
    return decorator
