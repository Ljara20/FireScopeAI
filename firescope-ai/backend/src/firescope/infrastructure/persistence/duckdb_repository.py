"""Read-only access to FireScope AI analytical Parquet datasets."""

from pathlib import Path
from typing import Any

import duckdb

DATASETS = {
    "daily_activity": "processed/firescope_usa_daily_activity.parquet",
    "harmonized": "harmonized/firescope_usa_harmonized.parquet",
    "calendar": "processed/firescope_usa_fire_calendar.parquet",
    "climatology": "processed/firescope_usa_fire_climatology.parquet",
    "anomalies": "processed/firescope_usa_fire_anomalies.parquet",
    "forecast_validation": (
        "processed/firescope_usa_fire_forecast_validation.parquet"
    ),
}

SENSORS = {"modis", "viirs_snpp", "viirs_noaa20"}


class DuckDbRepository:
    """Query approved analytical datasets without modifying source files."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).resolve()
        self.connection = duckdb.connect(":memory:")

    def _dataset_path(self, dataset: str) -> Path:
        if dataset not in DATASETS:
            raise ValueError(f"Unsupported dataset: {dataset}")

        path = self.data_dir / DATASETS[dataset]

        if not path.is_file():
            raise FileNotFoundError(f"Dataset not found: {path}")

        return path

    def query(
        self,
        dataset: str,
        *,
        sensor: str,
        state_code: str | None = None,
        year: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return bounded rows filtered by sensor and optionally state."""

        if sensor not in SENSORS:
            raise ValueError(f"Unsupported sensor: {sensor}")

        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")

        if offset < 0:
            raise ValueError("offset must be nonnegative")

        path = self._dataset_path(dataset)

        sql = """
            SELECT *
            FROM read_parquet(?)
            WHERE sensor = ?
        """
        parameters: list[Any] = [str(path), sensor]

        if state_code is not None:
            if len(state_code) != 2 or not state_code.isalpha():
                raise ValueError("state_code must contain two letters")

            sql += " AND state_code = ?"
            parameters.append(state_code.upper())

        order_columns = {
            "daily_activity": (
                "state_code, activity_date, h3_cell_id, spatial_status"
            ),
            "harmonized": (
                "state_code, activity_date, h3_cell_id, spatial_status"
            ),
            "calendar": "state_code, year, month",
            "climatology": "state_code, month",
            "anomalies": "state_code, year, month",
            "forecast_validation": "state_code, year, month",
        }

        if year is not None:
            if dataset not in {
                "calendar",
                "anomalies",
                "forecast_validation",
            }:
                raise ValueError(
                    f"Year filtering is unsupported for {dataset}"
                )

            if not 2000 <= year <= 2100:
                raise ValueError("year must be between 2000 and 2100")

            sql += " AND year = ?"
            parameters.append(year)

        sql += (
            f" ORDER BY {order_columns[dataset]} "
            "LIMIT ? OFFSET ?"
        )
        parameters.extend([limit, offset])

        result = self.connection.execute(sql, parameters)
        columns = [column[0] for column in result.description]

        return [
            dict(zip(columns, row, strict=True))
            for row in result.fetchall()
        ]

    def list_regions(self, *, sensor: str) -> list[dict[str, str]]:
        """List distinct states available for a specific sensor."""
        if sensor not in SENSORS:
            raise ValueError(f"Unsupported sensor: {sensor}")

        path = self._dataset_path("calendar")

        rows = self.connection.execute(
            """
            SELECT DISTINCT state_code, state_name
            FROM read_parquet(?)
            WHERE sensor = ?
              AND state_code IS NOT NULL
              AND state_name IS NOT NULL
            ORDER BY state_code, state_name
            """,
            [str(path), sensor],
        ).fetchall()

        return [
            {"state_code": code, "state_name": name}
            for code, name in rows
        ]

    def close(self) -> None:
        """Close the DuckDB connection."""
        self.connection.close()
