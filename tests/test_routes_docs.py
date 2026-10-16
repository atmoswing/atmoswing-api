from fastapi.testclient import TestClient
from atmoswing_api.app.main import app


client = TestClient(app)


def test_docs_export():
    response = client.get("/minidocs")
    assert response.status_code == 200
    assert "Documentation" in response.content.decode("utf-8")


def test_docs_export_lists_all_routes():
    html = client.get("/minidocs").text
    paths = app.openapi()["paths"]
    assert any(path.startswith("/forecasts/") for path in paths)
    for path in paths:
        assert f"<h2>{path}</h2>" in html


def test_docs_export_shows_details():
    html = client.get("/minidocs").text
    assert "Analog dates for a given forecast and target date" in html
    assert "Get the analog dates for a given region" in html
    assert "region, forecast_date, method, configuration, lead_time" in html
    assert "normalize (query)" in html
