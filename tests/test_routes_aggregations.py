import os
from functools import lru_cache
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app
from atmoswing_api.app.routes.aggregations import get_settings as original_get_settings


@lru_cache
def get_settings():
    cwd = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(cwd, "data")
    return config.Settings(data_dir=data_dir)

app.dependency_overrides[original_get_settings] = get_settings
client = TestClient(app)


def test_entities_analog_values_percentile_aggregation():
    response = client.get("/aggregations/adn/2024-10-05T00/4Zo-CEP/48/entities-values-percentile/90")
    assert response.status_code == 200
    data = response.json()
    assert "entity_ids" in data
    assert "values" in data
    assert "values_normalized" in data

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

def test_exception_file_not_found():
    @lru_cache
    def get_settings_wrong():
        cwd = os.path.dirname(os.path.abspath(__file__))
        data_dir_wrong = os.path.join(cwd, "data_wrong")
        return config.Settings(data_dir=data_dir_wrong)

    app.dependency_overrides[original_get_settings] = get_settings_wrong
    client_wrong = TestClient(app)

    response = client_wrong.get(
        "/aggregations/adn/2024-10-05T00/series-synthesis-per-method/90")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"].startswith("Region or forecast not found")