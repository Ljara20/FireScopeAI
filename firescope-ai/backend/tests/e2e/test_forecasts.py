"""End-to-end tests for retrospective forecast evaluation."""

from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


def test_forecasts_requires_sensor():
    response = client.get("/api/v1/forecasts")
    assert response.status_code == 422


def test_forecasts_rejects_unknown_sensor():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "unknown"},
    )
    assert response.status_code == 422


def test_forecasts_returns_historical_records():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "state_code": "AK", "year": 2000},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["sensor"] == "modis"
    assert payload["metric"] == "retrospective_detection_count_estimate"
    assert payload["count"] > 0


def test_forecasts_preserves_missing_estimates():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "state_code": "AK", "year": 2000},
    )

    assert response.status_code == 200

    records = response.json()["records"]
    assert records

    for record in records:
        assert record["independent_forecast_status"] == "outside_test"
        assert record["independent_forecast_detection_count"] is None


def test_forecasts_rejects_invalid_year():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "year": 1999},
    )
    assert response.status_code == 422


def test_forecasts_rejects_invalid_limit():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "limit": 1001},
    )
    assert response.status_code == 422


def test_forecasts_rejects_negative_offset():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "offset": -1},
    )
    assert response.status_code == 422


def test_forecasts_returns_empty_future_year():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "year": 2099},
    )

    assert response.status_code == 200
    assert response.json()["records"] == []
    assert response.json()["count"] == 0


def test_forecasts_normalizes_state_code():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "state_code": "ak", "year": 2000},
    )

    assert response.status_code == 200

    records = response.json()["records"]
    assert records
    assert all(record["state_code"] == "AK" for record in records)
