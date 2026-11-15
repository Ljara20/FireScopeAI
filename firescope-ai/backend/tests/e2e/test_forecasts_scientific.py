"""Scientific validation of retrospective forecast API."""

import duckdb
import pytest
from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)

PARQUET = "../data/processed/firescope_usa_fire_forecast_validation.parquet"

SENSORS = ("modis", "viirs_snpp", "viirs_noaa20")

EXPECTED_PREDICTIONS = {
    "modis": 1040,
    "viirs_snpp": 1145,
    "viirs_noaa20": 1156,
}

EXPECTED_STATUSES = {
    "independent_test_prediction",
    "insufficient_features",
    "outside_test",
}


def test_parquet_scientific_consistency():
    con = duckdb.connect()

    try:
        result = con.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(independent_forecast_detection_count) AS available,
                COUNT(*) FILTER (
                    WHERE independent_forecast_status =
                        'independent_test_prediction'
                ) AS test_predictions,
                COUNT(*) FILTER (
                    WHERE independent_forecast_status NOT IN (
                        'independent_test_prediction',
                        'insufficient_features',
                        'outside_test'
                    )
                    OR independent_forecast_status IS NULL
                ) AS invalid_status,
                COUNT(*) FILTER (
                    WHERE (
                        independent_forecast_status =
                            'independent_test_prediction'
                        AND independent_forecast_detection_count IS NULL
                    )
                    OR (
                        independent_forecast_status !=
                            'independent_test_prediction'
                        AND independent_forecast_detection_count IS NOT NULL
                    )
                ) AS invalid_prediction
            FROM read_parquet(?)
            """,
            [PARQUET],
        ).fetchone()
    finally:
        con.close()

    assert result == (26047, 3341, 3341, 0, 0)


@pytest.mark.parametrize("sensor", SENSORS)
def test_predictions_per_sensor(sensor):
    con = duckdb.connect()

    try:
        count = con.execute(
            """
            SELECT COUNT(*)
            FROM read_parquet(?)
            WHERE sensor = ?
              AND independent_forecast_status =
                  'independent_test_prediction'
              AND independent_forecast_detection_count IS NOT NULL
            """,
            [PARQUET, sensor],
        ).fetchone()[0]
    finally:
        con.close()

    assert count == EXPECTED_PREDICTIONS[sensor]


@pytest.mark.parametrize("sensor", SENSORS)
def test_api_matches_parquet(sensor):
    """Compare all API records against the source Parquet."""
    con = duckdb.connect()

    try:
        source = con.execute(
            """
            SELECT
                state_code,
                year,
                month,
                detection_count,
                independent_forecast_detection_count,
                independent_forecast_status
            FROM read_parquet(?)
            WHERE sensor = ?
            ORDER BY state_code, year, month
            """,
            [PARQUET, sensor],
        ).fetchall()
    finally:
        con.close()

    api_records = []

    for offset in range(0, len(source), 1000):
        response = client.get(
            "/api/v1/forecasts",
            params={
                "sensor": sensor,
                "limit": 1000,
                "offset": offset,
            },
        )

        assert response.status_code == 200, response.text

        payload = response.json()

        assert payload["sensor"] == sensor
        assert payload["count"] == len(payload["records"])

        api_records.extend(payload["records"])

    assert len(api_records) == len(source)

    api_records.sort(
        key=lambda record: (
            record["state_code"] is None,
            record["state_code"] or "",
            record["year"],
            record["month"],
        )
    )

    for record, expected in zip(api_records, source, strict=True):
        state_code, year, month, observed, prediction, status = expected

        assert record["state_code"] == state_code
        assert record["year"] == year
        assert record["month"] == month
        assert record["detection_count"] == observed
        assert record["independent_forecast_status"] == status

        actual_prediction = record["independent_forecast_detection_count"]

        if prediction is None:
            assert actual_prediction is None
        else:
            assert actual_prediction == pytest.approx(prediction)

        assert status in EXPECTED_STATUSES


@pytest.mark.parametrize("sensor", SENSORS)
def test_api_preserves_sensor_separation(sensor):
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": sensor, "limit": 100},
    )

    assert response.status_code == 200

    records = response.json()["records"]

    assert records
    assert all(record["sensor"] == sensor for record in records)


def test_api_does_not_claim_operational_forecasts():
    response = client.get(
        "/api/v1/forecasts",
        params={"sensor": "modis", "limit": 1},
    )

    assert response.status_code == 200

    payload = response.json()
    limitations = " ".join(payload["limitations"]).lower()

    assert "retrospective" in limitations
    assert "not future forecasts" in limitations
    assert "not individual wildfires" in limitations
    assert "null" in limitations
