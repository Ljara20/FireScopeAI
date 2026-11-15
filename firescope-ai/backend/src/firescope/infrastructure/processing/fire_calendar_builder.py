"""Historical sensor-specific fire activity calendar. No cross-sensor summation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import duckdb


class FireCalendarBuilder:
    REQUIRED = {
        "activity_date", "sensor", "state_code", "state_name",
        "detection_count", "valid_frp_count", "invalid_frp_count",
        "frp_sum_mw", "aligned_log_activity", "alignment_status",
    }

    def __init__(self, source: Path):
        self.source = Path(source)

    @staticmethod
    def _sql_path(path: Path) -> str:
        return "'" + str(path.resolve()).replace("'", "''") + "'"

    def run(self, destination: Path, climatology: Path, manifest: Path) -> dict[str, Any]:
        destination, climatology, manifest = map(Path, (destination, climatology, manifest))
        paths = [self.source.resolve(), destination.resolve(), climatology.resolve(), manifest.resolve()]
        if len(set(paths)) != len(paths):
            raise ValueError("Source, outputs and manifest must be different paths")
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        for p in (destination, climatology, manifest):
            p.parent.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect()
        try:
            con.execute(f"CREATE TEMP VIEW source_data AS SELECT * FROM read_parquet({self._sql_path(self.source)})")
            cols = {row[0] for row in con.execute("DESCRIBE source_data").fetchall()}
            missing = sorted(self.REQUIRED - cols)
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
            invalid = con.execute("""
                SELECT count(*) FROM source_data
                WHERE detection_count IS NULL OR detection_count < 0
                   OR valid_frp_count IS NULL OR invalid_frp_count IS NULL
                   OR valid_frp_count + invalid_frp_count <> detection_count
                   OR TRY_CAST(activity_date AS DATE) IS NULL
                   OR sensor IS NULL
            """).fetchone()[0]
            if invalid:
                raise ValueError(f"Invalid input rows: {invalid}")

            # State-level monthly observations. Never aggregate multiple sensors together.
            # NULL state codes are kept as explicit unassigned-state audit rows.
            con.execute("""
                CREATE TEMP VIEW monthly AS
                SELECT
                    CAST(state_code AS VARCHAR) AS state_code,
                    CAST(state_name AS VARCHAR) AS state_name,
                    CAST(sensor AS VARCHAR) AS sensor,
                    YEAR(CAST(activity_date AS DATE))::INTEGER AS year,
                    MONTH(CAST(activity_date AS DATE))::INTEGER AS month,
                    MAKE_DATE(YEAR(CAST(activity_date AS DATE)), MONTH(CAST(activity_date AS DATE)), 1) AS month_start,
                    COUNT(DISTINCT CAST(activity_date AS DATE))::INTEGER AS days_with_detections,
                    SUM(detection_count)::BIGINT AS detection_count,
                    SUM(valid_frp_count)::BIGINT AS valid_frp_count,
                    SUM(invalid_frp_count)::BIGINT AS invalid_frp_count,
                    SUM(frp_sum_mw)::DOUBLE AS frp_sum_mw,
                    -- A descriptive distribution statistic, NOT a sum of calibrated activity.
                    MEDIAN(aligned_log_activity)::DOUBLE AS median_daily_cell_aligned_log_activity,
                    COUNT(aligned_log_activity)::BIGINT AS aligned_daily_cell_groups,
                    CASE WHEN COUNT(*) FILTER (WHERE alignment_status = 'not_calibrated') > 0
                         THEN 'contains_not_calibrated'
                         WHEN COUNT(*) FILTER (WHERE alignment_status = 'validated_exploratory') > 0
                         THEN 'validated_exploratory'
                         ELSE 'reference' END AS alignment_status
                FROM source_data
                GROUP BY 1, 2, 3, 4, 5, 6
            """)
            con.execute("""
                CREATE TEMP VIEW climatology_view AS
                SELECT state_code, state_name, sensor, month,
                       COUNT(DISTINCT year)::INTEGER AS years_with_detections,
                       AVG(detection_count)::DOUBLE AS mean_monthly_detection_count_observed_years,
                       MEDIAN(detection_count)::DOUBLE AS median_monthly_detection_count_observed_years,
                       MIN(detection_count)::BIGINT AS min_monthly_detection_count_observed_years,
                       MAX(detection_count)::BIGINT AS max_monthly_detection_count_observed_years,
                       AVG(days_with_detections)::DOUBLE AS mean_days_with_detections_observed_years,
                       MEDIAN(median_daily_cell_aligned_log_activity)::DOUBLE
                           AS median_of_monthly_aligned_log_activity,
                       MIN(year)::INTEGER AS first_observed_year,
                       MAX(year)::INTEGER AS last_observed_year
                FROM monthly
                GROUP BY 1, 2, 3, 4
            """)
            input_groups, input_detections = con.execute(
                "SELECT count(*), COALESCE(sum(detection_count), 0) FROM source_data"
            ).fetchone()
            output_rows, output_detections = con.execute(
                "SELECT count(*), COALESCE(sum(detection_count), 0) FROM monthly"
            ).fetchone()
            if input_detections != output_detections:
                raise RuntimeError("Detection counts differ after calendar aggregation")
            unassigned = con.execute(
                "SELECT COALESCE(sum(detection_count),0) FROM monthly WHERE state_code IS NULL"
            ).fetchone()[0]
            by_sensor = dict(con.execute(
                "SELECT sensor, sum(detection_count)::BIGINT FROM monthly GROUP BY sensor ORDER BY sensor"
            ).fetchall())
            # Write temp files, then publish only once both exports have succeeded.
            tmp_monthly = destination.with_name(destination.name + '.tmp.parquet')
            tmp_clim = climatology.with_name(climatology.name + '.tmp.parquet')
            try:
                con.execute(f"COPY (SELECT * FROM monthly ORDER BY sensor, state_code, year, month) "
                            f"TO {self._sql_path(tmp_monthly)} (FORMAT PARQUET, COMPRESSION ZSTD)")
                con.execute(f"COPY (SELECT * FROM climatology_view ORDER BY sensor, state_code, month) "
                            f"TO {self._sql_path(tmp_clim)} (FORMAT PARQUET, COMPRESSION ZSTD)")
                tmp_monthly.replace(destination)
                tmp_clim.replace(climatology)
            finally:
                tmp_monthly.unlink(missing_ok=True)
                tmp_clim.unlink(missing_ok=True)
            climatology_rows = con.execute("SELECT count(*) FROM climatology_view").fetchone()[0]
            report = {
                "input": str(self.source.resolve()),
                "calendar_output": str(destination.resolve()),
                "climatology_output": str(climatology.resolve()),
                "input_daily_groups": input_groups,
                "calendar_monthly_groups": output_rows,
                "climatology_groups": climatology_rows,
                "input_detections": int(input_detections),
                "calendar_detections": int(output_detections),
                "unassigned_state_detections": int(unassigned),
                "detections_by_sensor": {str(k): int(v) for k, v in by_sensor.items()},
                "limitations": [
                    "Detections are satellite observations, not unique fires.",
                    "Only months/years with detections are present; absent periods are not zeros.",
                    "Climatology is conditional on observed detection months/years, not satellite coverage.",
                    "Sensors are never combined; aligned log activity is a descriptive median only.",
                    "FRP is not burned area or fire severity and is not calibrated across sensors.",
                ],
            }
            manifest.write_text(json.dumps(report, indent=2), encoding='utf-8')
            return report
        finally:
            con.close()
