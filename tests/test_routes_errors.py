import os
import pytest
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app
from atmoswing_api.app.routes import meta, forecasts, aggregations

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BASE = "/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord"


@pytest.fixture
def client():
    def get_settings():
        return config.Settings(data_dir=DATA_DIR)

    for module in (meta, forecasts, aggregations):
        app.dependency_overrides[module.get_settings] = get_settings

    return TestClient(app)


@pytest.mark.parametrize("url, message", [
    ("/forecasts/adn/2024-13-45/4Zo-CEP/Alpes_Nord/48/analog-dates",
     "Invalid date format (2024-13-45)"),
    ("/meta/adn/not-a-date/methods", "Invalid date format (not-a-date)"),
    (f"{BASE}/tomorrow/analog-dates", "Invalid lead time format (tomorrow)"),
    (f"{BASE}/999999/48/analogs", "Entity not found: 999999"),
    (f"{BASE}/48/entities-values-percentile/90?normalize=7", "normalize must be in"),
    ("/meta/%2E%2E/last-forecast-date", "Invalid region: '..'"),
])
def test_invalid_input_returns_400(client, url, message):
    response = client.get(url)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Invalid request")
    assert message in detail
    assert DATA_DIR not in detail


@pytest.mark.parametrize("url, message", [
    ("/meta/unknown/last-forecast-date", "Region not found: unknown"),
    ("/forecasts/adn/2024-10-06T00/4Zo-CEP/Unknown_Config/48/analog-dates",
     "No forecast found for 2024-10-06T00, method 4Zo-CEP and configuration Unknown_Config"),
    ("/forecasts/adn/2030-01-01T00/4Zo-CEP/Alpes_Nord/48/analog-dates",
     "No forecast found for 2030-01-01"),
    ("/aggregations/adn/2030-01-01T00/series-synthesis-total/90",
     "No forecast found for 2030-01-01"),
])
def test_missing_data_returns_400(client, url, message):
    response = client.get(url)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Region or forecast not found")
    assert message in detail
    assert DATA_DIR not in detail


def test_unexpected_error_returns_generic_500(client, monkeypatch):
    async def failing_service(*args, **kwargs):
        raise RuntimeError(f"Cannot read {DATA_DIR}/secret.nc")

    monkeypatch.setattr(forecasts, "get_analog_dates", failing_service)
    response = client.get(f"{BASE}/47/analog-dates")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}


def test_os_file_not_found_hides_message(client, monkeypatch):
    async def failing_service(*args, **kwargs):
        raise FileNotFoundError(f"{DATA_DIR}/adn/missing.nc")

    monkeypatch.setattr(forecasts, "get_analog_dates", failing_service)
    response = client.get(f"{BASE}/47/analog-dates")
    assert response.status_code == 400
    assert response.json() == {"detail": "Region or forecast not found"}
