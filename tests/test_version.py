import re
from pathlib import Path
from fastapi.testclient import TestClient
from atmoswing_api.__version__ import __version__
from atmoswing_api.app.main import app

PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_version_is_the_one_of_pyproject():
    # Fails when the package was installed before a version change: reinstall it
    # (pip install -e .) to update its metadata
    # tomllib is not available on Python 3.10
    match = re.search(r'^version = "([^"]+)"', PYPROJECT.read_text(encoding="utf-8"), re.M)
    assert __version__ == match.group(1)


def test_api_reports_the_package_version():
    assert TestClient(app).get("/openapi.json").json()["info"]["version"] == __version__
