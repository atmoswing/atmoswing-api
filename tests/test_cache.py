import socket
import pytest
from fastapi.testclient import TestClient
from atmoswing_api import cache
from atmoswing_api.app.main import app
from atmoswing_api.app.routes import forecasts


class FailingClient:
    def __init__(self, error):
        self.error = error

    async def ping(self):
        raise self.error

    async def get(self, key):
        raise self.error

    async def setex(self, key, ttl, value):
        raise self.error


class MemoryClient:
    def __init__(self):
        self.store = {}

    async def ping(self):
        return True

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, ttl, value):
        self.store[key] = value


@pytest.fixture
def restore_cache_state(monkeypatch):
    # monkeypatch restores the module globals modified by the tests
    monkeypatch.setattr(cache, "redis_available", True)
    monkeypatch.setattr(cache, "_redis_retry_at", 0.0)
    monkeypatch.setattr(cache, "redis_client", cache.redis_client)


def counting_function():
    calls = []

    @cache.redis_cache(ttl=60)
    async def func(value):
        calls.append(value)
        return {"value": value}

    return func, calls


async def test_cache_hit_skips_function(restore_cache_state, monkeypatch):
    monkeypatch.setattr(cache, "redis_client", MemoryClient())
    func, calls = counting_function()

    assert await func(1) == {"value": 1}
    assert await func(1) == {"value": 1}
    assert await func(2) == {"value": 2}
    assert calls == [1, 2]


@pytest.mark.parametrize("error", [
    ConnectionRefusedError("refused"),
    cache.RedisError("redis error"),
    RuntimeError("attached to a different loop"),
])
async def test_redis_errors_bypass_cache(restore_cache_state, monkeypatch, error):
    failing_client = FailingClient(error)
    monkeypatch.setattr(cache, "redis_client", failing_client)
    func, calls = counting_function()

    assert await func(1) == {"value": 1}
    assert await func(1) == {"value": 1}
    assert calls == [1, 1]
    assert cache.redis_available is False
    # A client bound to another event loop is replaced; others are kept
    assert (cache.redis_client is failing_client) != isinstance(error, RuntimeError)


async def test_check_connection_does_not_raise(restore_cache_state, monkeypatch):
    monkeypatch.setattr(cache, "redis_client", FailingClient(ConnectionRefusedError()))
    assert await cache.check_connection() is False


def redis_reachable():
    try:
        with socket.create_connection((cache.REDIS_HOST, cache.REDIS_PORT), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not redis_reachable(), reason="Redis is not reachable")
def test_route_served_from_redis(restore_cache_state, monkeypatch):
    # Use a new client: connections of the current one may be bound to the event
    # loop of a previous test
    monkeypatch.setattr(cache, "redis_client", cache._create_client())

    url = "/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/analog-dates"
    # The context manager runs the lifespan and keeps a single event loop
    with TestClient(app) as client:
        expected = client.get(url)
        assert expected.status_code == 200

        async def failing_service(*args, **kwargs):
            raise RuntimeError("The service should not be called")

        # The response can only come from Redis now
        monkeypatch.setattr(forecasts, "get_analog_dates", failing_service)
        response = client.get(url)
        assert response.status_code == 200
        assert response.json() == expected.json()
