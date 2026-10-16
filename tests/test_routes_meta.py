import os
from functools import lru_cache
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app
from atmoswing_api.config import get_settings


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

def test_list_relevant_entities():
    response = client.get("/meta/adn/2024-10-05T00/4Zo-CEP/Alpes_Nord/relevant-entities")
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data

def test_exception_file_not_found():
    @lru_cache
    def get_settings_wrong():
        cwd = os.path.dirname(os.path.abspath(__file__))
        data_dir_wrong = os.path.join(cwd, "data_wrong")
        return config.Settings(data_dir=data_dir_wrong)

    app.dependency_overrides[get_settings] = get_settings_wrong
    client_wrong = TestClient(app)

    response = client_wrong.get("/meta/adn/2024-10-05T00/methods")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"].startswith("Region or forecast not found")