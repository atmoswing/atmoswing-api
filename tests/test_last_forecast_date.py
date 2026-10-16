import os
import pytest
from atmoswing_api.app.utils.errors import DataNotFoundError
from atmoswing_api.app.utils.utils import get_last_forecast_date

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def add(tmp_path, relative_path):
    path = tmp_path / "reg" / relative_path
    if relative_path.endswith("/"):
        path.mkdir(parents=True, exist_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def last(tmp_path):
    return get_last_forecast_date(str(tmp_path), "reg")


@pytest.fixture
def forecasts(tmp_path):
    add(tmp_path, "2024/10/05/2024-10-05_00.4Zo-GFS.Alpes_Nord.nc")
    add(tmp_path, "2024/10/05/2024-10-05_06.4Zo-GFS.Alpes_Nord.nc")
    add(tmp_path, "2024/10/05/2024-10-05_06.4Zo-CEP.Alpes_Nord.nc")
    return tmp_path


def test_sample_data():
    assert get_last_forecast_date(DATA_DIR, "adn") == "2024-10-06T18"


def test_latest_hour(forecasts):
    assert last(forecasts) == "2024-10-05T06"


@pytest.mark.parametrize("stray", [
    ".DS_Store",
    ".prebuilt_cache/",
    "tmp/",
    "app.log",
    "9999",
    "2024/zz/",
    "2024/10/.DS_Store",
    "2024/10/99/",
    "2024/10/05/2024-10-05_18.4Zo-GFS.Alpes_Nord.nc.part",
    "2024/10/05/2024-10-05_18.4Zo-GFS.Alpes_Nord.nc~",
    "2024/10/05/2024-10-05_18.log",
    "2024/10/05/2024-10-05_18.nc",
    "2024/10/05/notes.txt",
    "2024/10/05/2024-10-05_18.4Zo-GFS.Alpes_Nord.nc/",
])
def test_stray_entries_are_ignored(forecasts, stray):
    add(forecasts, stray)
    assert last(forecasts) == "2024-10-05T06"


@pytest.mark.parametrize("empty", ["2024/10/06/", "2024/11/", "2025/"])
def test_empty_directories_fall_back_to_previous(forecasts, empty):
    add(forecasts, empty)
    assert last(forecasts) == "2024-10-05T06"


def test_files_of_other_dates_are_ignored(forecasts):
    # A file in the wrong directory does not point to a nonexistent forecast date
    add(forecasts, "2024/10/06/2024-10-07_00.4Zo-GFS.Alpes_Nord.nc")
    assert last(forecasts) == "2024-10-05T06"


def test_invalid_dates_are_ignored(forecasts):
    add(forecasts, "2024/13/01/2024-13-01_00.4Zo-GFS.Alpes_Nord.nc")
    add(forecasts, "2024/10/05/2024-10-05_25.4Zo-GFS.Alpes_Nord.nc")
    assert last(forecasts) == "2024-10-05T06"


def test_newer_month_and_year(forecasts):
    add(forecasts, "2024/11/01/2024-11-01_00.4Zo-GFS.Alpes_Nord.nc")
    assert last(forecasts) == "2024-11-01T00"
    add(forecasts, "2025/01/01/2025-01-01_12.4Zo-GFS.Alpes_Nord.nc")
    assert last(forecasts) == "2025-01-01T12"


@pytest.mark.parametrize("entries", [
    [],
    ["2024/10/05/"],
    ["2024/10/05/notes.txt", ".DS_Store"],
])
def test_no_forecast(tmp_path, entries):
    (tmp_path / "reg").mkdir()
    for entry in entries:
        add(tmp_path, entry)
    with pytest.raises(DataNotFoundError, match="No forecast found for region reg"):
        last(tmp_path)
