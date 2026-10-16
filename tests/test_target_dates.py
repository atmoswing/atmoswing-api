import os
from datetime import datetime
import pytest
import xarray as xr
from fastapi.testclient import TestClient
from atmoswing_api.app.main import app
from atmoswing_api.app.services import aggregations
from atmoswing_api.app.utils import utils

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DAY_PATH = os.path.join(DATA_DIR, "adn", "2024", "10", "06")
# Target dates: 2024-10-06T00 to 2024-10-13T00, daily
FILE_24H = os.path.join(DAY_PATH, "2024-10-06_18.4Zo-GFS.Alpes_Nord.nc")
FILE_29_STATIONS = os.path.join(DAY_PATH, "2024-10-06_18.2Z-06h-GFS.Alpes_Nord.nc")


@pytest.fixture(scope="module")
def ds():
    with xr.open_dataset(FILE_24H, engine="h5netcdf") as dataset:
        yield dataset


@pytest.mark.parametrize("target_date, expected", [
    ("2024-10-06T00", (0, datetime(2024, 10, 6))),
    ("2024-10-08T00", (2, datetime(2024, 10, 8))),
    ("2024-10-08T12", (2, datetime(2024, 10, 8))),  # last one before
    ("2024-10-13T00", (7, datetime(2024, 10, 13))),
    ("2024-10-05T18", None),  # before the first target date
    ("2024-10-01T00", None),
    ("2024-10-13T06", None),  # after the last target date
])
def test_get_target_date_index(ds, target_date, expected):
    assert utils.get_target_date_index(ds, target_date) == expected


def test_get_row_indices_before_first_target_date(ds):
    assert utils.get_row_indices(ds, "2024-10-01T00") is None


@pytest.mark.parametrize("url", [
    "/forecasts/adn/2024-10-06T18/4Zo-GFS/Alpes_Nord/2024-10-01/analog-dates",
    "/forecasts/adn/2024-10-06T18/4Zo-GFS/Alpes_Nord/2024-10-20/analog-dates",
    "/aggregations/adn/2024-10-06T18/4Zo-GFS/2024-10-01/entities-values-percentile/90",
])
def test_target_date_outside_forecast_returns_no_values(url):
    response = TestClient(app).get(url)
    assert response.status_code == 200
    data = response.json()
    assert data.get("analog_dates", data.get("values")) == []


def test_configurations_with_different_stations(monkeypatch):
    monkeypatch.setattr(utils, "list_forecast_files", lambda *args: (
        "2024-10-06T18", [FILE_24H, FILE_29_STATIONS]))
    with pytest.raises(ValueError, match="stations of 2024-10-06_18.2Z-06h-GFS"):
        aggregations._get_entities_analog_values_percentile(
            DATA_DIR, "adn", "2024-10-06T18", "4Zo-GFS", 24, 90)
