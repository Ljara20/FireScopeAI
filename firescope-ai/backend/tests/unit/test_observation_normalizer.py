from pathlib import Path
import duckdb
import pytest

from firescope.infrastructure.processing.observation_normalizer import ObservationNormalizer


def test_normalization_preserves_rows_and_sensor_semantics(tmp_path: Path):
    source, target, report = (tmp_path / x for x in ('input.parquet', 'output.parquet', 'report.json'))
    con = duckdb.connect()
    con.execute("""
        COPY (SELECT * FROM (VALUES
          ('modis', 40.0, -100.0, '2020-01-01', 5, 10.0, '85'),
          ('viirs_snpp', 41.0, -101.0, '2020-01-02', 2359, -1.0, 'n'),
          ('viirs_noaa20', 999.0, -101.0, '2020-01-03', 2460, 3.0, 'h')
        ) AS t(source_sensor, latitude, longitude, acq_date, acq_time, frp, confidence))
        TO ? (FORMAT PARQUET)
    """, [str(source)])
    con.close()
    result = ObservationNormalizer(source).run(target, report)
    assert sum(r['observations'] for r in result['sensors']) == 3
    con = duckdb.connect()
    rows = con.execute("""SELECT sensor_normalized, frp_mw, modis_confidence_pct,
        viirs_confidence_class, coordinates_status, acquisition_time_utc
        FROM read_parquet(?) ORDER BY source_sensor""", [str(target)]).fetchall()
    assert rows[0][2] == 85.0
    assert str(rows[0][5]) == '00:05:00'
    assert rows[1][4] == 'invalid'
    assert rows[1][5] is None
    assert rows[2][1] is None
    assert rows[2][3] == 'n'
    assert con.execute('SELECT COUNT(*) FROM read_parquet(?)', [str(target)]).fetchone()[0] == 3
    con.close()


def test_missing_columns(tmp_path: Path):
    source = tmp_path / 'bad.parquet'
    con = duckdb.connect()
    con.execute('COPY (SELECT 1 AS latitude) TO ? (FORMAT PARQUET)', [str(source)])
    con.close()
    with pytest.raises(ValueError, match='Missing required columns'):
        ObservationNormalizer(source).run(tmp_path / 'out.parquet', tmp_path / 'report.json')


def test_prevent_input_overwrite(tmp_path: Path):
    source = tmp_path / 'input.parquet'
    source.touch()
    with pytest.raises(ValueError, match='overwrite'):
        ObservationNormalizer(source).run(source, tmp_path / 'report.json')
