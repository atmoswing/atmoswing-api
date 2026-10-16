import json
import os
import pytest
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app
from atmoswing_api.app.routes import common
from atmoswing_api.app.utils.errors import InvalidInputError
from atmoswing_api.app.utils.utils import compute_cache_hash, make_cache_paths

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.fixture(autouse=True)
def clear_latest_cache():
    common._latest_forecast_dates.clear()
    yield
    common._latest_forecast_dates.clear()


def add_forecast_file(data_dir, region, forecast_date, name="4Zo-GFS.Alpes_Nord"):
    day, hour = forecast_date.split("T")
    path = data_dir / region / day[:4] / day[5:7] / day[8:10]
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{day}_{hour}.{name}.nc").touch()


@pytest.mark.parametrize("value, expected", [
    ("2024-10-05", "2024-10-05T00"),
    ("2024-10-05T06", "2024-10-05T06"),
    ("latest", "2024-10-06T18"),
])
async def test_resolve_forecast_date(value, expected):
    assert await common.resolve_forecast_date(DATA_DIR, "adn", value) == expected


async def test_resolve_forecast_date_invalid():
    with pytest.raises(InvalidInputError):
        await common.resolve_forecast_date(DATA_DIR, "adn", "2024-13-45")


async def test_latest_is_reused_within_ttl(tmp_path, monkeypatch):
    add_forecast_file(tmp_path, "reg", "2024-10-05T00")
    assert await common.resolve_forecast_date(str(tmp_path), "reg", "latest") == "2024-10-05T00"

    add_forecast_file(tmp_path, "reg", "2024-10-05T06")
    assert await common.resolve_forecast_date(str(tmp_path), "reg", "latest") == "2024-10-05T00"

    monkeypatch.setattr(common, "LATEST_FORECAST_DATE_TTL", 0)
    assert await common.resolve_forecast_date(str(tmp_path), "reg", "latest") == "2024-10-05T06"


async def test_resolve_latest_passes_resolved_date():
    received = {}

    async def route(region, forecast_date, settings):
        received["forecast_date"] = forecast_date
        return "ok"

    wrapped = common.resolve_latest(route)
    settings = config.Settings(data_dir=DATA_DIR)
    assert await wrapped(region="adn", forecast_date="latest", settings=settings) == "ok"
    assert received["forecast_date"] == "2024-10-06T18"


def test_route_latest_returns_resolved_date():
    response = TestClient(app).get("/meta/adn/latest/has-forecasts")
    assert response.status_code == 200
    assert response.json()["parameters"]["forecast_date"] == "2024-10-06T18:00:00"


def test_route_latest_unknown_region_returns_400():
    response = TestClient(app).get("/meta/unknown/latest/methods")
    assert response.status_code == 400
    assert response.json()["detail"] == "Region or forecast not found (Region not found: unknown)"


@pytest.mark.parametrize("forecast_date", ["latest", "2024-10-05T06", "2024-10-05T6"])
def test_route_uses_prebuilt_cache_for_resolved_date(tmp_path, forecast_date,
                                                    use_data_dir):
    # The forecast file is empty: the response can only come from the prebuilt cache
    add_forecast_file(tmp_path, "reg", "2024-10-05T06")
    prebuilt = {
        "parameters": {"region": "reg", "forecast_date": "2024-10-05T06:00:00"},
        "methods": [{"id": "4Zo-GFS", "name": "Prebuilt method"}],
    }
    prebuilt_dir = tmp_path / ".prebuilt_cache"
    prebuilt_dir.mkdir()
    hash_suffix = compute_cache_hash("list_methods", "reg", "2024-10-05T06")
    cache_path = make_cache_paths(prebuilt_dir, "list_methods", "reg", "2024-10-05T06",
                                  hash_suffix)
    cache_path.write_text(json.dumps({"result": prebuilt}), encoding="utf-8")

    use_data_dir(tmp_path)
    response = TestClient(app).get(f"/meta/reg/{forecast_date}/methods")
    assert response.status_code == 200
    assert response.json() == prebuilt
