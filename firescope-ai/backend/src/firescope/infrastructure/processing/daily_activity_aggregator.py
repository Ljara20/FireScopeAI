"""Aggregate georeferenced FIRMS detections into sensor/day/H3 activity bins."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import duckdb


class DailyActivityAggregator:
    """Out-of-core DuckDB aggregation; preserves sensor provenance."""

    REQUIRED = {
        "sensor_normalized", "acquisition_date", "h3_cell_id",
        "state_code", "spatial_status", "frp_mw", "frp_status",
    }

    def __init__(self, source: Path):
        self.source = Path(source)
        if not self.source.is_file():
            raise FileNotFoundError(self.source)

    @staticmethod
    def _quote(path: Path) -> str:
        return "'" + str(path.resolve()).replace("'", "''") + "'"

    def run(self, destination: Path, manifest: Path) -> dict[str, Any]:
        destination, manifest = Path(destination), Path(manifest)
        if destination.resolve() == self.source.resolve():
            raise ValueError("Destination cannot overwrite the source")
        if destination.resolve() == manifest.resolve():
            raise ValueError("Destination and manifest must differ")
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(destination.name + ".tmp.parquet")
        con = duckdb.connect()
        try:
            con.execute(f"CREATE TEMP VIEW observations AS SELECT * FROM read_parquet({self._quote(self.source)})")
            columns = {row[0] for row in con.execute("DESCRIBE observations").fetchall()}
            missing = sorted(self.REQUIRED - columns)
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
            if "state_name" not in columns:
                raise ValueError("Missing required column: state_name")
            con.execute("""
                CREATE TEMP VIEW daily_activity AS
                SELECT
                    CAST(acquisition_date AS DATE) AS activity_date,
                    CAST(sensor_normalized AS VARCHAR) AS sensor,
                    CAST(h3_cell_id AS VARCHAR) AS h3_cell_id,
                    CAST(state_code AS VARCHAR) AS state_code,
                    CAST(state_name AS VARCHAR) AS state_name,
                    CAST(spatial_status AS VARCHAR) AS spatial_status,
                    COUNT(*)::BIGINT AS detection_count,
                    COUNT(*) FILTER (WHERE frp_status = 'valid' AND frp_mw IS NOT NULL)::BIGINT AS valid_frp_count,
                    COUNT(*) FILTER (WHERE frp_status <> 'valid' OR frp_mw IS NULL)::BIGINT AS invalid_frp_count,
                    SUM(frp_mw) FILTER (WHERE frp_status = 'valid' AND frp_mw IS NOT NULL) AS frp_sum_mw,
                    AVG(frp_mw) FILTER (WHERE frp_status = 'valid' AND frp_mw IS NOT NULL) AS frp_mean_mw,
                    MEDIAN(frp_mw) FILTER (WHERE frp_status = 'valid' AND frp_mw IS NOT NULL) AS frp_median_mw,
                    MAX(frp_mw) FILTER (WHERE frp_status = 'valid' AND frp_mw IS NOT NULL) AS frp_max_mw
                FROM observations
                GROUP BY 1, 2, 3, 4, 5, 6
            """)
            # Date/sensor and location-null bins are retained for auditing.
            metrics = con.execute("""
                SELECT COUNT(*)::BIGINT AS groups,
                       COALESCE(SUM(detection_count),0)::BIGINT AS observations,
                       COALESCE(SUM(invalid_frp_count),0)::BIGINT AS invalid_frp,
                       COALESCE(SUM(CASE WHEN h3_cell_id IS NULL THEN detection_count ELSE 0 END),0)::BIGINT AS without_h3,
                       COALESCE(SUM(CASE WHEN activity_date IS NULL THEN detection_count ELSE 0 END),0)::BIGINT AS without_date
                FROM daily_activity
            """).fetchone()
            source_count = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            if metrics[1] != source_count:
                raise RuntimeError(f"Count mismatch: {metrics[1]} vs {source_count}")
            sensor_rows = con.execute("""
                SELECT sensor, SUM(detection_count)::BIGINT
                FROM daily_activity GROUP BY sensor ORDER BY sensor
            """).fetchall()
            try:
                con.execute(f"COPY (SELECT * FROM daily_activity) TO {self._quote(temp)} (FORMAT PARQUET, COMPRESSION ZSTD)")
                temp.replace(destination)
            finally:
                temp.unlink(missing_ok=True)
            result = {
                "input": str(self.source), "output": str(destination),
                "source_observations": source_count, "aggregated_observations": metrics[1],
                "daily_groups": metrics[0], "invalid_frp_observations": metrics[2],
                "observations_without_h3": metrics[3], "observations_without_date": metrics[4],
                "observations_by_sensor": {str(sensor): count for sensor, count in sensor_rows},
                "grouping_keys": ["activity_date", "sensor", "h3_cell_id", "state_code", "state_name", "spatial_status"],
                "notes": [
                    "Counts are satellite detections, not unique fires or burned area.",
                    "MODIS and VIIRS remain separate; no scientific calibration has been applied.",
                    "Only dates with observations appear; absent dates do not imply zero fires or complete satellite coverage.",
                    "Null dates and H3 cells are retained in audit groups.",
                    "FRP sums are descriptive and not comparable across sensors without calibration.",
                ],
            }
            manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result
        finally:
            con.close()
