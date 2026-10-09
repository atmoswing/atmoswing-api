import os
import pytest
from atmoswing_api.app.main import app
from atmoswing_api.config import Settings, get_settings

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _use_data_dir(data_dir):
    app.dependency_overrides[get_settings] = lambda: Settings(data_dir=str(data_dir))


@pytest.fixture(autouse=True)
def test_data_dir():
    """
    Make the routes use the test data directory, and restore the dependency
    overrides after each test so that tests cannot affect each other.
    """
    overrides = dict(app.dependency_overrides)
    _use_data_dir(DATA_DIR)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(overrides)


@pytest.fixture
def use_data_dir():
    """Function making the routes use another data directory during a test."""
    return _use_data_dir
