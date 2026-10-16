import pytest
from fastapi.testclient import TestClient
from limits import parse
from atmoswing_api.app import limiter
from atmoswing_api.app.main import app


@pytest.fixture
def small_budget(monkeypatch):
    monkeypatch.setattr(limiter, "application_limit", parse("5/minute"))


def statuses(client, urls):
    return [client.get(url).status_code for url in urls]


def test_budget_shared_by_all_routes(small_budget):
    client = TestClient(app)
    urls = [f"/meta/adn/2024-10-05T{hour:02d}/has-forecasts" for hour in range(5)]
    assert statuses(client, urls) == [200] * 5
    assert statuses(client, ["/meta/show-config", urls[0], "/unknown"]) == [429] * 3


def test_budget_per_client(small_budget):
    first = TestClient(app, client=("192.0.2.1", 50000))
    second = TestClient(app, client=("192.0.2.2", 50000))
    assert statuses(first, ["/meta/show-config"] * 6)[-1] == 429
    assert statuses(second, ["/meta/show-config"]) == [200]


def test_rate_limit_response(small_budget):
    client = TestClient(app)
    statuses(client, ["/meta/show-config"] * 5)
    response = client.get("/meta/show-config")
    assert response.status_code == 429
    assert response.json() == {"detail": limiter.RATE_LIMIT_MESSAGE}
    assert 1 <= int(response.headers["Retry-After"]) <= 60


def test_default_budget_is_not_hit_by_normal_use():
    client = TestClient(app)
    assert statuses(client, ["/meta/show-config"] * 150) == [200] * 150


def test_minidocs_route_limit():
    client = TestClient(app)
    assert statuses(client, ["/minidocs"] * 10) == [200] * 10
    response = client.get("/minidocs")
    assert response.status_code == 429
    assert response.json() == {"detail": limiter.RATE_LIMIT_MESSAGE}
    assert "Retry-After" in response.headers
    # Other routes are not affected by the route limit
    assert client.get("/meta/show-config").status_code == 200


def test_health_is_not_rate_limited(small_budget):
    client = TestClient(app)
    assert statuses(client, ["/health"] * 10) == [200] * 10
    assert client.get("/health").json() == {"status": "ok"}
    assert statuses(client, ["/meta/show-config"] * 5) == [200] * 5
