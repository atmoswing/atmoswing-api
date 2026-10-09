import os
import pytest
from fastapi.testclient import TestClient
from atmoswing_api.app.main import app
from atmoswing_api.app.utils.errors import InvalidInputError, DataNotFoundError
from atmoswing_api.app.utils.utils import (validate_path_component, check_region_path,
                                           get_file_path, get_files_pattern)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REGION_PATH = os.path.join(DATA_DIR, "adn")
INVALID_NAMES = ["", ".", "..", ".prebuilt_cache", "a/b", "..\\..", "a\0b"]


@pytest.mark.parametrize("name", ["adn", "4Zo-GFS", "Alpes_Nord", "2Z-24h-GFS"])
def test_validate_path_component_valid(name):
    assert validate_path_component(name) == name


@pytest.mark.parametrize("name", INVALID_NAMES)
def test_validate_path_component_invalid(name):
    with pytest.raises(InvalidInputError):
        validate_path_component(name)


def test_check_region_path_valid():
    assert check_region_path(DATA_DIR, "adn") == str(os.path.realpath(REGION_PATH))


@pytest.mark.parametrize("region", INVALID_NAMES)
def test_check_region_path_invalid(region):
    with pytest.raises(InvalidInputError):
        check_region_path(DATA_DIR, region)


@pytest.mark.parametrize("region", ["missing", "app.log"])
def test_check_region_path_missing(region):
    with pytest.raises(DataNotFoundError):
        check_region_path(DATA_DIR, region)


@pytest.mark.parametrize("method, configuration", [
    ("..", "Alpes_Nord"), ("4Zo-GFS", ".."), ("..\\..\\x", "Alpes_Nord"),
    ("4Zo-GFS", "a/b")])
def test_get_file_path_invalid(method, configuration):
    with pytest.raises(InvalidInputError):
        get_file_path(REGION_PATH, "2024-10-05T00", method, configuration)


def test_get_files_pattern_escapes_method():
    pattern = get_files_pattern(REGION_PATH, "2024-10-05T00", "4Zo-*")
    assert "4Zo-[*]" in pattern


def test_get_files_pattern_invalid_method():
    with pytest.raises(InvalidInputError):
        get_files_pattern(REGION_PATH, "2024-10-05T00", "..")


@pytest.mark.parametrize("url", [
    "/meta/%2E%2E/last-forecast-date",
    "/meta/%2E%2E/2024-10-05T00/methods",
    "/meta/.prebuilt_cache/last-forecast-date",
    "/forecasts/%2E%2E/2024-10-05T00/4Zo-GFS/Alpes_Nord/24/analog-dates",
    "/forecasts/adn/2024-10-05T00/%2E%2E/Alpes_Nord/24/analog-dates",
    "/forecasts/adn/2024-10-05T00/4Zo-GFS/..%5C..%5Cx/24/analog-dates",
    "/aggregations/%2E%2E/2024-10-05T00/series-synthesis-total/90",
])
def test_routes_reject_path_traversal(url):
    response = TestClient(app).get(url)
    assert response.status_code == 400
    assert DATA_DIR not in response.text
    assert os.path.dirname(DATA_DIR) not in response.text
