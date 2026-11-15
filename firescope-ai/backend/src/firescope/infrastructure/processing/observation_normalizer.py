"""Lossless, sensor-aware technical normalization of FIRMS observations."""
from __future__ import annotations

import json
from pathlib import Path
import duckdb


class ObservationNormalizer:
    REQUIRED = {'source_sensor', 'latitude', 'longitude', 'acq_date', 'acq_time', 'frp', 'confidence'}
    SENSOR_MAP = {'modis': 'modis', 'viirs_snpp': 'viirs_snpp', 'viirs_noaa20': 'viirs_noaa20', 'viirs_jpss1': 'viirs_noaa20'}

    def __init__(self, input_path: Path):
        self.input_path = Path(input_path)
        if not self.input_path.is_file():
            raise FileNotFoundError(self.input_path)

    @staticmethod
    def _sql_path(path: Path) -> str:
        return "'" + str(path.resolve()).replace("'", "''") + "'"

    def run(self, output_path: Path, report_path: Path) -> dict:
        output_path, report_path = Path(output_path), Path(report_path)
        if output_path.resolve() == self.input_path.resolve():
            raise ValueError('Output must not overwrite input')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        try:
            con.execute(f"CREATE TEMP VIEW raw AS SELECT * FROM read_parquet({self._sql_path(self.input_path)})")
            columns = {row[0] for row in con.execute('DESCRIBE raw').fetchall()}
            missing = sorted(self.REQUIRED - columns)
            if missing:
                raise ValueError(f'Missing required columns: {missing}')
            # Preserve every original field. Additional columns carry normalized semantics.
            # FIRMS acquisition time is HHMM, sometimes encoded as integer (e.g. 5 => 00:05).
            con.execute("""
                CREATE TEMP VIEW typed AS SELECT *,
                    lower(trim(CAST(source_sensor AS VARCHAR))) AS _sensor_raw,
                    TRY_CAST(latitude AS DOUBLE) AS _lat,
                    TRY_CAST(longitude AS DOUBLE) AS _lon,
                    TRY_CAST(acq_date AS DATE) AS _day,
                    TRY_CAST(frp AS DOUBLE) AS _frp,
                    lower(trim(CAST(confidence AS VARCHAR))) AS _confidence,
                    lpad(trim(CAST(acq_time AS VARCHAR)), 4, '0') AS _hhmm
                FROM raw
            """)
            con.execute("""
                CREATE TEMP VIEW normalized AS SELECT * EXCLUDE (_sensor_raw, _lat, _lon, _day, _frp, _confidence, _hhmm),
                    CASE _sensor_raw
                        WHEN 'modis' THEN 'modis'
                        WHEN 'viirs_snpp' THEN 'viirs_snpp'
                        WHEN 'viirs_noaa20' THEN 'viirs_noaa20'
                        WHEN 'viirs_jpss1' THEN 'viirs_noaa20'
                        ELSE NULL END AS sensor_normalized,
                    CASE WHEN _lat BETWEEN -90 AND 90 AND isfinite(_lat) THEN _lat END AS latitude_normalized,
                    CASE WHEN _lon BETWEEN -180 AND 180 AND isfinite(_lon) THEN _lon END AS longitude_normalized,
                    _day AS acquisition_date,
                    CASE WHEN length(_hhmm) = 4 AND try_cast(substr(_hhmm,1,2) AS INTEGER) BETWEEN 0 AND 23
                          AND try_cast(substr(_hhmm,3,2) AS INTEGER) BETWEEN 0 AND 59
                         THEN try_cast(substr(_hhmm,1,2) || ':' || substr(_hhmm,3,2) || ':00' AS TIME)
                    END AS acquisition_time_utc,
                    CASE WHEN _frp >= 0 AND isfinite(_frp) THEN _frp END AS frp_mw,
                    CASE WHEN _sensor_raw = 'modis' AND try_cast(_confidence AS DOUBLE) BETWEEN 0 AND 100
                         THEN try_cast(_confidence AS DOUBLE) END AS modis_confidence_pct,
                    CASE WHEN _sensor_raw IN ('viirs_snpp','viirs_noaa20','viirs_jpss1')
                              AND _confidence IN ('l','n','h') THEN _confidence END AS viirs_confidence_class,
                    CASE WHEN _sensor_raw = 'modis' AND try_cast(_confidence AS DOUBLE) BETWEEN 0 AND 100 THEN 'valid'
                         WHEN _sensor_raw IN ('viirs_snpp','viirs_noaa20','viirs_jpss1')
                              AND _confidence IN ('l','n','h') THEN 'valid'
                         ELSE 'invalid_or_unknown' END AS confidence_status,
                    CASE WHEN _frp IS NULL THEN 'missing_or_non_numeric'
                         WHEN NOT isfinite(_frp) OR _frp < 0 THEN 'invalid'
                         ELSE 'valid' END AS frp_status,
                    CASE WHEN _lat BETWEEN -90 AND 90 AND isfinite(_lat)
                              AND _lon BETWEEN -180 AND 180 AND isfinite(_lon) THEN 'valid'
                         ELSE 'invalid' END AS coordinates_status,
                    CASE WHEN _day IS NOT NULL THEN 'valid' ELSE 'invalid' END AS date_status
                FROM typed
            """)
            # No row is removed; no cross-sensor confidence scale is invented.
            summary = con.execute("""
                SELECT sensor_normalized, count(*) AS observations,
                    count_if(frp_status <> 'valid') AS invalid_frp,
                    count_if(confidence_status <> 'valid') AS invalid_confidence,
                    count_if(coordinates_status <> 'valid') AS invalid_coordinates,
                    count_if(date_status <> 'valid') AS invalid_dates,
                    count_if(acquisition_time_utc IS NULL) AS invalid_times
                FROM normalized GROUP BY 1 ORDER BY 1
            """).fetchall()
            # Export atomically: a failed COPY cannot replace a previous successful output.
            temp_output = output_path.with_name(output_path.name + '.tmp.parquet')
            try:
                con.execute(f"COPY (SELECT * FROM normalized) TO {self._sql_path(temp_output)} (FORMAT PARQUET, COMPRESSION ZSTD)")
                temp_output.replace(output_path)
            finally:
                temp_output.unlink(missing_ok=True)
            report = {
                'input': str(self.input_path), 'output': str(output_path),
                'notes': ['All source rows and columns preserved.',
                          'FRP is MW, not burned area or fire severity.',
                          'MODIS percentage and VIIRS categorical confidence are not interchangeable.',
                          'No automatic deduplication or scientific harmonization performed.'],
                'sensors': [dict(zip(('sensor','observations','invalid_frp','invalid_confidence',
                                      'invalid_coordinates','invalid_dates','invalid_times'), row)) for row in summary]
            }
            report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
            return report
        finally:
            con.close()
