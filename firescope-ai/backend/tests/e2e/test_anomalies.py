"""End-to-end tests for historical anomalies."""

from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


def test_anomalies_requires_sensor():
    response = client.get("/api/v1/anomalies")
    assert response.status_code == 422


def test_anomalies_rejects_invalid_sensor():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "unknown"},
    )
    assert response.status_code == 422


def test_anomalies_returns_historical_records():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "state_code": "AK", "year": 2000},
    )

    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["sensor"] == "modis"
    assert payload["count"] == len(payload["records"])
    assert payload["records"]

    for record in payload["records"]:
        assert record["sensor"] == "modis"
        assert record["state_code"] == "AK"
        assert record["year"] == 2000


def test_anomalies_preserves_null_baseline():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "state_code": "AK", "year": 2000},
    )

    assert response.status_code == 200, response.text

    records = response.json()["records"]

    insufficient = [
        record
        for record in records
        if record["anomaly_class"] == "insufficient_baseline"
    ]

    assert insufficient

    for record in insufficient:
        assert record["anomaly_assessable"] is False
        assert record["historical_z_score"] is None


def test_anomalies_rejects_invalid_year():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "year": 1900},
    )
    assert response.status_code == 422


def test_anomalies_rejects_invalid_limit():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "limit": 0},
    )
    assert response.status_code == 422


def test_anomalies_rejects_negative_offset():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "offset": -1},
    )
    assert response.status_code == 422


def test_anomalies_returns_empty_future_year():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "year": 2099},
    )

    assert response.status_code == 200, response.text
    assert response.json()["records"] == []


def test_anomalies_normalizes_state_code():
    response = client.get(
        "/api/v1/anomalies",
        params={"sensor": "modis", "state_code": "ak", "year": 2000},
    )

    assert response.status_code == 200, response.text
    assert response.json()["records"]

    for record in response.json()["records"]:
        assert record["state_code"] == "AK"
