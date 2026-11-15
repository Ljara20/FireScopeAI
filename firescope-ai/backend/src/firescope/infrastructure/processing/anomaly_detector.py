"""Sensor-specific retrospective anomalies against strictly prior-year baselines."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import duckdb


class AnomalyDetector:
    REQUIRED = {'state_code', 'state_name', 'sensor', 'year', 'month',
                'detection_count', 'baseline_years', 'historical_mean',
                'historical_std', 'historical_z_score', 'has_minimum_baseline'}

    def __init__(self, source: Path, warning_z: float = 2.0, extreme_z: float = 3.0):
        self.source = Path(source)
        if not (0 < warning_z < extreme_z):
            raise ValueError('Thresholds must satisfy 0 < warning_z < extreme_z')
        self.warning_z = float(warning_z)
        self.extreme_z = float(extreme_z)

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
            con.execute(f'CREATE TEMP VIEW features AS SELECT * FROM read_parquet({self.quote(self.source)})')
            columns = {r[0] for r in con.execute('DESCRIBE features').fetchall()}
            if missing := sorted(self.REQUIRED - columns):
                raise ValueError(f'Missing required columns: {missing}')
            bad = con.execute('''SELECT count(*) FROM features WHERE
                sensor IS NULL OR year IS NULL OR month IS NULL OR month NOT BETWEEN 1 AND 12
                OR detection_count IS NULL OR detection_count < 0
                OR baseline_years IS NULL OR baseline_years < 0
                OR (historical_std IS NOT NULL AND historical_std < 0)
                OR (has_minimum_baseline AND baseline_years < 3)''').fetchone()[0]
            if bad:
                raise ValueError(f'Invalid feature rows: {bad}')
            duplicates = con.execute('''SELECT count(*) FROM (
                SELECT state_code, sensor, year, month FROM features
                GROUP BY ALL HAVING count(*) > 1)''').fetchone()[0]
            if duplicates:
                raise ValueError(f'Duplicate state/sensor/month keys: {duplicates}')
            # No baseline / zero variance => unassessable, not normal or anomalous.
            con.execute(f'''CREATE TEMP VIEW classified AS
                SELECT *,
                  CASE WHEN NOT has_minimum_baseline OR baseline_years < 3
                         OR historical_mean IS NULL OR historical_std IS NULL
                         OR historical_std <= 0 OR historical_z_score IS NULL
                         OR NOT isfinite(historical_z_score)
                    THEN 'insufficient_baseline'
                    WHEN historical_z_score >= {self.extreme_z} THEN 'extreme_high'
                    WHEN historical_z_score >= {self.warning_z} THEN 'high'
                    WHEN historical_z_score <= -{self.extreme_z} THEN 'extreme_low'
                    WHEN historical_z_score <= -{self.warning_z} THEN 'low'
                    ELSE 'typical' END AS anomaly_class,
                  CASE WHEN has_minimum_baseline AND baseline_years >= 3
                         AND historical_std > 0 AND historical_z_score IS NOT NULL
                         AND isfinite(historical_z_score)
                    THEN TRUE ELSE FALSE END AS anomaly_assessable,
                  'prior_year_same_month_zscore' AS anomaly_method
                FROM features''')
            n_in, total_in = con.execute('SELECT count(*), sum(detection_count) FROM features').fetchone()
            n_out, total_out = con.execute('SELECT count(*), sum(detection_count) FROM classified').fetchone()
            if (n_in, total_in) != (n_out, total_out):
                raise RuntimeError('Classification changed row/detection counts')
            classes = dict(con.execute('SELECT anomaly_class, count(*) FROM classified GROUP BY 1').fetchall())
            by_sensor = {sensor: dict(con.execute('SELECT anomaly_class, count(*) FROM classified WHERE sensor = ? GROUP BY 1', [sensor]).fetchall())
                         for (sensor,) in con.execute('SELECT DISTINCT sensor FROM classified ORDER BY 1').fetchall()}
            tmp = destination.with_name(destination.name + '.tmp.parquet')
            try:
                con.execute(f'COPY (SELECT * FROM classified ORDER BY sensor, state_code, year, month) TO {self.quote(tmp)} (FORMAT PARQUET, COMPRESSION ZSTD)')
                tmp.replace(destination)
            finally:
                tmp.unlink(missing_ok=True)
            report = {
                'input': str(self.source.resolve()), 'output': str(destination.resolve()),
                'input_rows': n_in, 'output_rows': n_out, 'detections_preserved': int(total_out or 0),
                'anomaly_classes': classes, 'classes_by_sensor': by_sensor,
                'thresholds': {'warning_abs_z': self.warning_z, 'extreme_abs_z': self.extreme_z},
                'method': 'Retrospective z-score from same-state/sensor/calendar-month prior years only',
                'limitations': [
                    'Only observed detection months are represented; missing periods are not zeros.',
                    'Zero-variance or fewer than three historical years => insufficient_baseline.',
                    'High/low describe relative satellite detections, not fire risk, probability or severity.',
                    'Normality of historical counts is not assumed; z thresholds are heuristic, not p-values.',
                    'Sensors are classified independently; orbital coverage and detection bias are not corrected.',
                    'Current-month detection_count is used for retrospective detection; not a forecast.'
                ]}
            manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            return report
        finally:
            con.close()
