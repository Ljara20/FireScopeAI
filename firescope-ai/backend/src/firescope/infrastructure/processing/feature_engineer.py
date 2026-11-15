"""Leakage-aware, sensor-specific monthly feature engineering.

Missing months are missing observations, never inferred zero-fire months.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import duckdb


class FeatureEngineer:
    REQUIRED = {'state_code', 'state_name', 'sensor', 'year', 'month',
                'detection_count', 'days_with_detections', 'frp_sum_mw',
                'median_daily_cell_aligned_log_activity', 'alignment_status'}

    def __init__(self, source: Path):
        self.source = Path(source)

    @staticmethod
    def quote(path: Path) -> str:
        return "'" + str(path.resolve()).replace("'", "''") + "'"

    def run(self, destination: Path, manifest: Path) -> dict[str, Any]:
        destination, manifest = Path(destination), Path(manifest)
        if len({self.source.resolve(), destination.resolve(), manifest.resolve()}) != 3:
            raise ValueError('Source, destination and manifest must differ')
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        try:
            con.execute(f'CREATE TEMP VIEW raw AS SELECT * FROM read_parquet({self.quote(self.source)})')
            cols = {r[0] for r in con.execute('DESCRIBE raw').fetchall()}
            if missing := sorted(self.REQUIRED - cols):
                raise ValueError(f'Missing required columns: {missing}')
            bad = con.execute('''SELECT count(*) FROM raw WHERE sensor IS NULL OR year NOT BETWEEN 1990 AND 2100
                OR month NOT BETWEEN 1 AND 12 OR detection_count IS NULL OR detection_count < 0
                OR days_with_detections IS NULL OR days_with_detections < 0''').fetchone()[0]
            if bad:
                raise ValueError(f'Invalid calendar rows: {bad}')
            duplicates = con.execute('''SELECT count(*) FROM (
                SELECT state_code, sensor, year, month FROM raw
                GROUP BY ALL HAVING count(*) > 1)''').fetchone()[0]
            if duplicates:
                raise ValueError(f'Duplicate state/sensor/month keys: {duplicates}')
            # Baseline is computed ONLY from earlier years, never current/future years.
            # Lags are null if the immediately preceding calendar month is absent.
            con.execute('''CREATE TEMP VIEW features AS
            WITH base AS (
              SELECT *, MAKE_DATE(year::INTEGER, month::INTEGER, 1) AS feature_month,
                     LN(1.0 + detection_count) AS log1p_detection_count,
                     SIN(2.0 * PI() * month / 12.0) AS month_sin,
                     COS(2.0 * PI() * month / 12.0) AS month_cos
              FROM raw
            ), history AS (
              SELECT b.*,
                LAG(feature_month, 1) OVER w AS previous_month,
                LAG(detection_count, 1) OVER w AS previous_count,
                LAG(feature_month, 2) OVER w AS previous_2_month,
                LAG(detection_count, 2) OVER w AS previous_2_count,
                COUNT(*) OVER (PARTITION BY state_code, sensor, month ORDER BY year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS baseline_years,
                AVG(detection_count) OVER (PARTITION BY state_code, sensor, month ORDER BY year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historical_mean,
                STDDEV_SAMP(detection_count) OVER (PARTITION BY state_code, sensor, month ORDER BY year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historical_std,
                MEDIAN(detection_count) OVER (PARTITION BY state_code, sensor, month ORDER BY year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historical_median
              FROM base b
              WINDOW w AS (PARTITION BY state_code, sensor ORDER BY feature_month)
            )
            SELECT state_code, state_name, sensor, year, month, feature_month,
              detection_count, days_with_detections, frp_sum_mw,
              median_daily_cell_aligned_log_activity, alignment_status,
              log1p_detection_count, month_sin, month_cos,
              CASE WHEN previous_month = feature_month - INTERVAL 1 MONTH
                THEN previous_count END AS lag_1_month_detections,
              CASE WHEN previous_2_month = feature_month - INTERVAL 2 MONTH
                THEN previous_2_count END AS lag_2_month_detections,
              baseline_years, historical_mean, historical_std, historical_median,
              CASE WHEN baseline_years >= 3 AND historical_mean > 0
                THEN detection_count / historical_mean END AS historical_activity_ratio,
              CASE WHEN baseline_years >= 3 AND historical_std > 0
                THEN (detection_count - historical_mean) / historical_std END AS historical_z_score,
              CASE WHEN baseline_years >= 3 THEN TRUE ELSE FALSE END AS has_minimum_baseline,
              CASE WHEN previous_month = feature_month - INTERVAL 1 MONTH
                THEN TRUE ELSE FALSE END AS has_consecutive_previous_month
            FROM history''')
            n_in, total_in = con.execute('SELECT count(*), sum(detection_count) FROM raw').fetchone()
            n_out, total_out = con.execute('SELECT count(*), sum(detection_count) FROM features').fetchone()
            if (n_in, total_in) != (n_out, total_out):
                raise RuntimeError('Feature generation changed row/detection counts')
            stats = con.execute('''SELECT count(*) FILTER (WHERE has_minimum_baseline),
                count(*) FILTER (WHERE has_consecutive_previous_month),
                count(*) FILTER (WHERE historical_z_score IS NOT NULL)
                FROM features''').fetchone()
            temp = destination.with_name(destination.name + '.tmp.parquet')
            try:
                con.execute(f'COPY (SELECT * FROM features ORDER BY sensor, state_code, year, month) TO {self.quote(temp)} (FORMAT PARQUET, COMPRESSION ZSTD)')
                temp.replace(destination)
            finally:
                temp.unlink(missing_ok=True)
            report = {
                'input': str(self.source.resolve()), 'output': str(destination.resolve()),
                'input_rows': n_in, 'output_rows': n_out, 'detections_preserved': int(total_out),
                'rows_with_prior_year_baseline_at_least_3': stats[0],
                'rows_with_consecutive_previous_month': stats[1],
                'rows_with_historical_z_score': stats[2],
                'baseline': 'Same state, sensor and calendar month; strictly prior years only; minimum 3 observed years',
                'limitations': [
                    'Missing months are not imputed as zero; absent observations are not confirmed inactivity.',
                    'Historical baseline is conditional on months with detections, not satellite coverage.',
                    'Sensor-specific features are not cross-sensor fire equivalence.',
                    'Features describe observed satellite activity, not fire probability or severity.',
                    'No future target is constructed in this phase.'
                ]
            }
            manifest.write_text(json.dumps(report, indent=2), encoding='utf-8')
            return report
        finally:
            con.close()
