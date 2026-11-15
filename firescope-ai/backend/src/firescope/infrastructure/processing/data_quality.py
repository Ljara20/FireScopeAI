"""Read-only DuckDB quality profiling for NASA FIRMS observation Parquet."""
from __future__ import annotations

from pathlib import Path
import duckdb


class FireDataQualityProfiler:
    """Compute sensor-aware quality metrics without materializing observations."""

    REQUIRED = frozenset({'source_sensor', 'latitude', 'longitude', 'acq_date', 'frp'})

    def __init__(self, parquet_path: Path):
        self.parquet_path = Path(parquet_path)
        if not self.parquet_path.is_file():
            raise FileNotFoundError(self.parquet_path)

    def run(self, output_dir: Path) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        try:
            # The path is an escaped SQL literal: CREATE VIEW does not accept bind params.
            path = str(self.parquet_path.resolve()).replace("'", "''")
            con.execute(f"CREATE TEMP VIEW raw AS SELECT * FROM read_parquet('{path}')")
            columns = {row[0] for row in con.execute('DESCRIBE raw').fetchall()}
            missing = sorted(self.REQUIRED - columns)
            if missing:
                raise ValueError(f'Missing required columns: {missing}')
            def field(name: str) -> str:
                return f'CAST("{name}" AS VARCHAR)' if name in columns else 'NULL::VARCHAR'
            con.execute(f"""
                CREATE TEMP VIEW clean AS SELECT
                  {field('source_sensor')} AS sensor,
                  TRY_CAST({field('latitude')} AS DOUBLE) AS lat,
                  TRY_CAST({field('longitude')} AS DOUBLE) AS lon,
                  TRY_CAST({field('acq_date')} AS DATE) AS day,
                  TRY_CAST({field('frp')} AS DOUBLE) AS power,
                  {field('confidence')} AS confidence,
                  {field('acq_time')} AS acq_time,
                  {field('satellite')} AS satellite,
                  {field('instrument')} AS instrument,
                  {field('daynight')} AS daynight
                FROM raw
            """)
            reports = {
                'sensor_quality.csv': """
                  SELECT COALESCE(sensor,'UNKNOWN') AS sensor, COUNT(*) AS observations,
                    COUNT_IF(lat IS NULL OR lon IS NULL OR lat NOT BETWEEN -90 AND 90 OR lon NOT BETWEEN -180 AND 180) AS invalid_coordinates,
                    COUNT_IF(day IS NULL) AS invalid_dates,
                    COUNT_IF(power IS NULL) AS missing_or_non_numeric_frp,
                    COUNT_IF(power < 0 OR NOT isfinite(power)) AS invalid_frp,
                    COUNT_IF(confidence IS NULL OR trim(confidence) = '') AS missing_confidence,
                    MIN(day) AS first_date, MAX(day) AS last_date,
                    MIN(power) FILTER (WHERE power >= 0 AND isfinite(power)) AS min_frp,
                    MAX(power) FILTER (WHERE power >= 0 AND isfinite(power)) AS max_frp,
                    MEDIAN(power) FILTER (WHERE power >= 0 AND isfinite(power)) AS median_frp,
                    QUANTILE_CONT(power, 0.95) FILTER (WHERE power >= 0 AND isfinite(power)) AS p95_frp
                  FROM clean GROUP BY 1 ORDER BY 1
                """,
                'monthly_coverage.csv': """
                  SELECT COALESCE(sensor,'UNKNOWN') AS sensor,
                    YEAR(day) AS year, MONTH(day) AS month,
                    COUNT(*) AS observations, COUNT(DISTINCT day) AS days_with_detections,
                    COUNT_IF(power IS NOT NULL AND power >= 0 AND isfinite(power)) AS valid_frp_count
                  FROM clean WHERE day IS NOT NULL
                  GROUP BY 1,2,3 ORDER BY 1,2,3
                """,
                'confidence_distribution.csv': """
                  SELECT COALESCE(sensor,'UNKNOWN') AS sensor,
                    COALESCE(NULLIF(trim(confidence),''),'MISSING') AS confidence,
                    COUNT(*) AS observations
                  FROM clean GROUP BY 1,2 ORDER BY 1,3 DESC
                """,
                'potential_duplicates.csv': """
                  SELECT COALESCE(sensor,'UNKNOWN') AS sensor,
                    COUNT(*) AS duplicate_groups,
                    SUM(n-1) AS extra_rows_in_duplicate_groups
                  FROM (
                    SELECT sensor, day, acq_time, lat, lon, satellite, instrument, COUNT(*) n
                    FROM clean WHERE day IS NOT NULL AND lat IS NOT NULL AND lon IS NOT NULL
                    GROUP BY ALL HAVING COUNT(*) > 1
                  ) GROUP BY 1 ORDER BY 1
                """,
                'annual_coverage.csv': """
                  SELECT COALESCE(sensor,'UNKNOWN') AS sensor, YEAR(day) AS year,
                    COUNT(*) AS observations, COUNT(DISTINCT day) AS days_with_detections,
                    COUNT(DISTINCT MONTH(day)) AS months_with_detections
                  FROM clean WHERE day IS NOT NULL GROUP BY 1,2 ORDER BY 1,2
                """,
            }
            for filename, query in reports.items():
                destination = str((output_dir / filename).resolve()).replace("'", "''")
                con.execute(f"COPY ({query}) TO '{destination}' (HEADER, DELIMITER ',')")
            total = con.execute('SELECT COUNT(*) FROM clean').fetchone()[0]
            return {'input': str(self.parquet_path), 'total_observations': total,
                    'reports': sorted(reports), 'notes': [
                        'Raw observations are not harmonized or independent fire events.',
                        'Days/months without detections do not prove sensor coverage or missing data.',
                        'Duplicate candidates use same sensor, date, time, coordinates, satellite and instrument; review before removal.',
                        'FRP is radiative power, not burned area or damage.',
                    ]}
        finally:
            con.close()
