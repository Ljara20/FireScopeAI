"""Scientific consistency tests for preparedness."""

import duckdb
import pytest
from fastapi.testclient import TestClient

from firescope.presentation.api.main import app

client = TestClient(app)

PARQUET = "../data/processed/firescope_usa_fire_climatology.parquet"

SENSORS = ("modis", "viirs_snpp", "viirs_noaa20")


@pytest.mark.parametrize("sensor", SENSORS)
def test_api_matches_climatology(sensor):
    con = duckdb.connect()

    try:
        source = con.execute(
            """
            SELECT
                state_code,
                month,
                years_with_detections,
                mean_monthly_detection_count_observed_years
            FROM read_parquet(?)
            WHERE sensor = ?
            ORDER BY state_code NULLS LAST, month
            """,
            [PARQUET, sensor],
        ).fetchall()
    finally:
        con.close()

    records = []

    for offset in range(0, len(source), 1000):
        response = client.get(
            "/api/v1/preparedness",
            params={
                "sensor": sensor,
                "limit": 1000,
                "offset": offset,
            },
        )

        assert response.status_code == 200, response.text
        records.extend(response.json()["records"])

    assert len(records) == len(source)

    records.sort(
        key=lambda row: (
            row["state_code"] is None,
            row["state_code"] or "",
            row["month"],
        )
    )

    for record, expected in zip(records, source, strict=True):
        state_code, month, years, mean = expected

        assert record["state_code"] == state_code
        assert record["month"] == month
        assert record["years_with_detections"] == years
        assert record[
            "mean_monthly_detection_count_observed_years"
        ] == pytest.approx(mean)


def test_climatology_has_no_invalid_records():
    con = duckdb.connect()

    try:
        total, invalid = con.execute(
            """
            SELECT
                COUNT(*),
                COUNT(*) FILTER (
                    WHERE years_with_detections < 1
                       OR first_observed_year > last_observed_year
                       OR month NOT BETWEEN 1 AND 12
                )
            FROM read_parquet(?)
            """,
            [PARQUET],
        ).fetchone()
    finally:
        con.close()

    assert total == 1838
    assert invalid == 0
