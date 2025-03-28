import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from atmoswing_api.app.main import app  # Import your FastAPI app

client = TestClient(app)

def test_last_forecast_date():
    response = client.get("/meta/adn/last-forecast-date")
    assert response.status_code == 200
    data = response.json()
    assert "last_forecast_date" in data

def test_list_methods():
    response = client.get("/meta/adn/2024-10-05T00/methods")
    assert response.status_code == 200
    data = response.json()
    assert "methods" in data

def test_list_methods_and_configs():
    response = client.get("/meta/adn/2024-10-05T00/methods-and-configs")
    assert response.status_code == 200
    data = response.json()
    assert "methods" in data

def test_list_entities():
    response = client.get("/meta/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/entities")
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data

def test_analog_dates():
    response = client.get("/forecasts/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/2024-10-07/analog-dates")
    assert response.status_code == 200
    data = response.json()
    assert "analog_dates" in data

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

def test_entities_analog_values_percentile_aggregation():
    response = client.get("/aggregations/adn/2024-10-05T00/4Zo-CEP/48/entities-values-percentile/90")
    assert response.status_code == 200
    data = response.json()
    assert "entity_ids" in data
    assert "values" in data

def test_series_synthesis_per_method():
    response = client.get("/aggregations/adn/2024-10-05T00/series-synthesis-per-method/90")
    assert response.status_code == 200
    data = response.json()
    assert "series_percentiles" in data

def test_series_synthesis_total():
    response = client.get("/aggregations/adn/2024-10-05T00/series-synthesis-total/90")
    assert response.status_code == 200
    data = response.json()
    assert "series_percentiles" in data