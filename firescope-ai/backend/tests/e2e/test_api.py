"""Basic API integration tests."""

from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "firescope-api",
        "version": "0.1.0",
    }


def test_openapi_schema() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "FireScope AI API"
    assert schema["info"]["version"] == "0.1.0"


def test_existing_routes_are_registered() -> None:
    expected_routes = (
        "/api/v1/regions",
        "/api/v1/calendar",
        "/api/v1/forecasts",
        "/api/v1/preparedness",
    )

    schema = client.get("/openapi.json").json()

    for route in expected_routes:
        assert route in schema["paths"]
