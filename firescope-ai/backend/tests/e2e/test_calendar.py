"""Tests for the historical monthly calendar endpoint."""

from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


def test_calendar_requires_sensor() -> None:
    response = client.get("/api/v1/calendar")
    assert response.status_code == 422


def test_calendar_rejects_invalid_sensor() -> None:
    response = client.get("/api/v1/calendar?sensor=unknown")
    assert response.status_code == 422


def test_calendar_returns_historical_data() -> None:
    response = client.get(
        "/api/v1/calendar",
        params={
            "sensor": "modis",
            "state_code": "CA",
            "year": 2024,
            "limit": 12,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["schema_version"] == "1.0.0"
    assert payload["sensor"] == "modis"
    assert payload["count"] == len(payload["records"])
    assert payload["count"] > 0

    for record in payload["records"]:
        assert record["sensor"] == "modis"
        assert record["state_code"] == "CA"
        assert record["year"] == 2024
        assert record["detection_count"] >= 0


def test_calendar_rejects_invalid_year() -> None:
    response = client.get(
        "/api/v1/calendar?sensor=modis&year=1900"
    )
    assert response.status_code == 422


def test_calendar_rejects_invalid_limit() -> None:
    response = client.get(
        "/api/v1/calendar?sensor=modis&limit=1001"
    )
    assert response.status_code == 422


def test_calendar_rejects_invalid_state() -> None:
    response = client.get(
        "/api/v1/calendar?sensor=modis&state_code=California"
    )
    assert response.status_code == 422


def test_calendar_pagination() -> None:
    params = {
        "sensor": "modis",
        "state_code": "CA",
        "limit": 5,
    }

    first = client.get(
        "/api/v1/calendar",
        params={**params, "offset": 0},
    )

    second = client.get(
        "/api/v1/calendar",
        params={**params, "offset": 5},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_records = first.json()["records"]
    second_records = second.json()["records"]

    assert first_records
    assert second_records
    assert first_records != second_records


def test_calendar_preserves_sensor_separation() -> None:
    for sensor in ("modis", "viirs_snpp", "viirs_noaa20"):
        response = client.get(
            "/api/v1/calendar",
            params={"sensor": sensor, "limit": 5},
        )

        assert response.status_code == 200

        records = response.json()["records"]

        assert all(
            record["sensor"] == sensor
            for record in records
        )


def test_calendar_returns_empty_for_future_year() -> None:
    response = client.get(
        "/api/v1/calendar",
        params={
            "sensor": "modis",
            "state_code": "CA",
            "year": 2099,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["records"] == []
    assert payload["count"] == 0


def test_calendar_rejects_negative_offset() -> None:
    response = client.get(
        "/api/v1/calendar?sensor=modis&offset=-1"
    )

    assert response.status_code == 422


def test_calendar_rejects_zero_limit() -> None:
    response = client.get(
        "/api/v1/calendar?sensor=modis&limit=0"
    )

    assert response.status_code == 422


def test_calendar_normalizes_lowercase_state() -> None:
    response = client.get(
        "/api/v1/calendar",
        params={
            "sensor": "modis",
            "state_code": "ca",
            "year": 2024,
        },
    )

    assert response.status_code == 200

    records = response.json()["records"]

    assert records
    assert all(record["state_code"] == "CA" for record in records)
