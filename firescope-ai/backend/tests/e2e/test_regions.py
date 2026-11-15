"""Tests for the historical regions endpoint."""

from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


def test_regions_requires_sensor() -> None:
    response = client.get("/api/v1/regions")
    assert response.status_code == 422


def test_regions_rejects_unknown_sensor() -> None:
    response = client.get("/api/v1/regions?sensor=unknown")
    assert response.status_code == 422


def test_regions_returns_historical_states() -> None:
    response = client.get("/api/v1/regions?sensor=modis")

    assert response.status_code == 200

    payload = response.json()

    assert payload["schema_version"] == "1.0.0"
    assert payload["sensor"] == "modis"
    assert payload["count"] == len(payload["regions"])
    assert payload["count"] > 0
    assert any(
        region["state_code"] == "CA"
        for region in payload["regions"]
    )


def test_regions_are_sorted() -> None:
    response = client.get("/api/v1/regions?sensor=viirs_snpp")

    assert response.status_code == 200

    codes = [
        region["state_code"]
        for region in response.json()["regions"]
    ]

    assert codes == sorted(codes)
