import os
from functools import lru_cache
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app
from atmoswing_api.app.routes.forecasts import get_settings as original_get_settings


@lru_cache
def get_settings():
    cwd = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(cwd, "data")
    return config.Settings(data_dir=data_dir)

app.dependency_overrides[original_get_settings] = get_settings
client = TestClient(app)


def test_analog_dates():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/analog-dates")
    assert response.status_code == 200
    data = response.json()
    assert "analog_dates" in data

def test_analog_dates_lead_time_hours():
    response_1 = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/analog-dates")
    response_2 = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/48/analog-dates")
    assert response_2.status_code == 200
    data_1 = response_1.json()
    data_2 = response_2.json()
    assert data_1 == data_2

def test_analog_dates_lead_time_hours_round_down():
    response_1 = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/48/analog-dates")
    response_2 = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/50/analog-dates")
    assert response_2.status_code == 200
    data_1 = response_1.json()
    data_2 = response_2.json()
    assert data_1 == data_2

def test_analog_criteria():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/analogy-criteria")
    assert response.status_code == 200
    data = response.json()
    assert "criteria" in data

def test_entities_analog_values_percentile():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/entities-values-percentile/90")
    assert response.status_code == 200
    data = response.json()
    assert "entity_ids" in data
    assert "values" in data

def test_reference_values():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/reference-values")
    assert response.status_code == 200
    data = response.json()
    assert "reference_values" in data

def test_series_analog_values_best():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/series-values-best-analogs?number=10")
    assert response.status_code == 200
    data = response.json()
    assert "series_values" in data

def test_series_analog_values_percentiles():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/series-values-percentiles")
    assert response.status_code == 200
    data = response.json()
    assert "series_values" in data

def test_series_analog_values_percentiles_history():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/series-values-percentiles-history?number=5")
    assert response.status_code == 200
    data = response.json()
    assert "past_forecasts" in data

def test_analogs():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/1/48/analogs")
    assert response.status_code == 200
    data = response.json()
    assert "analogs" in data

def test_analog_values():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/1/48/analog-values")
    assert response.status_code == 200
    data = response.json()
    assert "values" in data

def test_analog_values_percentiles():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/1/48/analog-values-percentiles?percentiles=20&percentiles=60&percentiles=90")
    assert response.status_code == 200
    data = response.json()
    assert "values" in data

def test_analog_values_best():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/1/48/analog-values-best?number=10")
    assert response.status_code == 200
    data = response.json()
    assert "values" in data

def test_exception_file_not_found():
    @lru_cache
    def get_settings_wrong():
        cwd = os.path.dirname(os.path.abspath(__file__))
        data_dir_wrong = os.path.join(cwd, "data_wrong")
        return config.Settings(data_dir=data_dir_wrong)

    app.dependency_overrides[original_get_settings] = get_settings_wrong
    client_wrong = TestClient(app)

    response = client_wrong.get(
        "/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/3/reference-values")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"].startswith("Region or forecast not found")