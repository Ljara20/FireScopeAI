"""Tests for the read-only analytical repository."""

from pathlib import Path

import duckdb
import pytest

from firescope.infrastructure.persistence.duckdb_repository import (
    DuckDbRepository,
)


@pytest.fixture
def repository(tmp_path: Path):
    processed = tmp_path / "processed"
    processed.mkdir()

    path = processed / "firescope_usa_fire_calendar.parquet"

    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        COPY (
            SELECT
                'CA' AS state_code,
                'California' AS state_name,
                'modis' AS sensor,
                2024 AS year,
                7 AS month,
                100::BIGINT AS detection_count
            UNION ALL
            SELECT
                'TX', 'Texas', 'viirs_snpp', 2024, 7, 200::BIGINT
        )
        TO ? (FORMAT PARQUET)
        """,
        [str(path)],
    )
    connection.close()

    repo = DuckDbRepository(tmp_path)

    yield repo

    repo.close()


def test_query_filters_by_sensor(repository):
    rows = repository.query("calendar", sensor="modis")

    assert len(rows) == 1
    assert rows[0]["state_code"] == "CA"
    assert rows[0]["detection_count"] == 100


def test_query_filters_by_state(repository):
    rows = repository.query(
        "calendar",
        sensor="modis",
        state_code="ca",
    )

    assert len(rows) == 1
    assert rows[0]["state_code"] == "CA"


def test_query_returns_empty_for_missing_state(repository):
    rows = repository.query(
        "calendar",
        sensor="modis",
        state_code="NY",
    )

    assert rows == []


@pytest.mark.parametrize(
    "sensor",
    ["unknown", "", "modis' OR 1=1 --"],
)
def test_query_rejects_invalid_sensor(repository, sensor):
    with pytest.raises(ValueError):
        repository.query("calendar", sensor=sensor)


def test_query_rejects_unknown_dataset(repository):
    with pytest.raises(ValueError):
        repository.query("unknown", sensor="modis")


@pytest.mark.parametrize("limit", [0, -1, 1001])
def test_query_rejects_invalid_limit(repository, limit):
    with pytest.raises(ValueError):
        repository.query("calendar", sensor="modis", limit=limit)


def test_query_rejects_negative_offset(repository):
    with pytest.raises(ValueError):
        repository.query("calendar", sensor="modis", offset=-1)


def test_pagination_is_deterministic(repository):
    """Repeated queries must return identical pages."""
    first = repository.query(
        "calendar",
        sensor="modis",
        limit=1,
        offset=0,
    )

    repeated = repository.query(
        "calendar",
        sensor="modis",
        limit=1,
        offset=0,
    )

    assert first == repeated


def test_pagination_does_not_repeat_rows(repository):
    """Adjacent pages must not repeat the same records."""
    first = repository.query(
        "calendar",
        sensor="modis",
        limit=1,
        offset=0,
    )

    second = repository.query(
        "calendar",
        sensor="modis",
        limit=1,
        offset=1,
    )

    assert first
    assert second == []


def test_query_rejects_invalid_state_code(repository):
    """Invalid state identifiers must be rejected."""
    for state_code in ["California", "123", "C'", ""]:
        with pytest.raises(ValueError):
            repository.query(
                "calendar",
                sensor="modis",
                state_code=state_code,
            )


def test_query_preserves_sensor_separation(repository):
    """Results must belong exclusively to the requested sensor."""
    for sensor in ("modis", "viirs_snpp"):
        rows = repository.query(
            "calendar",
            sensor=sensor,
        )

        assert rows
        assert all(row["sensor"] == sensor for row in rows)


def test_query_missing_dataset_file(repository):
    """A missing approved dataset must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        repository.query(
            "climatology",
            sensor="modis",
        )
