import os
from functools import lru_cache
from fastapi.testclient import TestClient
from atmoswing_api import config
from atmoswing_api.app.main import app


client = TestClient(app)


def test_docs_export():
    response = client.get("/minidocs")
    assert response.status_code == 200
    assert "Documentation" in response.content.decode("utf-8")
