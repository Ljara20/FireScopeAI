"""Tests for the historical preparedness endpoint."""

import pytest
from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)


@pytest.mark.parametrize("sensor", ["modis", "viirs_snpp", "viirs_noaa20"])
def test_historical_data(sensor):
    response = client.get(
        "/api/v1/preparedness",
        params={"sensor": sensor, "state_code": "CA"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sensor"] == sensor
    assert data["records"]
    assert data["count"] == len(data["records"])
    assert all(r["state_code"] == "CA" for r in data["records"])


def test_sensor_required():
    assert client.get("/api/v1/preparedness").status_code == 422


def test_invalid_sensor():
    response = client.get(
        "/api/v1/preparedness", params={"sensor": "invalid"}
    )
    assert response.status_code == 422


def test_lowercase_state():
    response = client.get(
        "/api/v1/preparedness",
        params={"sensor": "modis", "state_code": "ca"},
    )
    assert response.status_code == 200
    assert all(r["state_code"] == "CA" for r in response.json()["records"])


def test_empty_result():
    response = client.get(
        "/api/v1/preparedness",
        params={"sensor": "modis", "state_code": "ZZ"},
    )
    assert response.status_code == 200
    assert response.json()["records"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"sensor": "modis", "limit": 0},
        {"sensor": "modis", "limit": 1001},
        {"sensor": "modis", "offset": -1},
        {"sensor": "modis", "state_code": "California"},
    ],
)
def test_invalid_parameters(params):
    response = client.get("/api/v1/preparedness", params=params)
    assert response.status_code == 422


def test_scientific_limitations():
    response = client.get(
        "/api/v1/preparedness", params={"sensor": "modis"}
    )
    assert response.status_code == 200
    limitations = " ".join(response.json()["limitations"]).lower()
    assert "not wildfire risk" in limitations
    assert "not individual wildfires" in limitations
