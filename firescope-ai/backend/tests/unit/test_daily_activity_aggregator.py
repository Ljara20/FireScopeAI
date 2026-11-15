"""Unit tests for phase 2.4. Run: python3 -m pytest tests/unit/test_daily_activity_aggregator.py -v"""
from pathlib import Path
import duckdb
import pytest

from firescope.infrastructure.processing.daily_activity_aggregator import DailyActivityAggregator


def _sample(path: Path) -> None:
    con = duckdb.connect()
    try:
        target = DailyActivityAggregator._quote(path)
        con.execute(f"""
            COPY (
                SELECT * FROM (VALUES
                    ('modis', DATE '2024-08-01', '85283473fffffff', 'CA', 'California', 'assigned', 10.0, 'valid'),
                    ('modis', DATE '2024-08-01', '85283473fffffff', 'CA', 'California', 'assigned', 20.0, 'valid'),
                    ('viirs_snpp', DATE '2024-08-01', '85283473fffffff', 'CA', 'California', 'assigned', 2.0, 'valid'),
                    ('modis', DATE '2024-08-02', '85283473fffffff', 'CA', 'California', 'assigned', NULL, 'invalid'),
                    ('viirs_noaa20', DATE '2024-08-02', '85283473fffffff', NULL, NULL, 'outside_state_polygons', 3.0, 'valid')
                ) AS t(sensor_normalized, acquisition_date, h3_cell_id, state_code, state_name, spatial_status, frp_mw, frp_status)
            ) TO {target} (FORMAT PARQUET)
        """)
    finally:
        con.close()


def test_aggregation_preserves_counts_and_sensor_separation(tmp_path):
    source, output, report = (tmp_path / x for x in ('source.parquet', 'daily.parquet', 'manifest.json'))
    _sample(source)
    result = DailyActivityAggregator(source).run(output, report)
    assert result['source_observations'] == result['aggregated_observations'] == 5
    assert result['daily_groups'] == 4
    assert result['invalid_frp_observations'] == 1
    con = duckdb.connect()
    try:
        rows = con.execute("SELECT sensor, detection_count, valid_frp_count, invalid_frp_count, frp_sum_mw FROM read_parquet(?) WHERE sensor = 'modis' ORDER BY activity_date", [str(output)]).fetchall()
        assert rows == [('modis', 2, 2, 0, 30.0), ('modis', 1, 0, 1, None)]
    finally:
        con.close()
    assert report.is_file()


def test_prevent_overwrite(tmp_path):
    source = tmp_path / 'source.parquet'
    _sample(source)
    with pytest.raises(ValueError, match='overwrite'):
        DailyActivityAggregator(source).run(source, tmp_path / 'report.json')


def test_missing_columns(tmp_path):
    source = tmp_path / 'source.parquet'
    con = duckdb.connect()
    try:
        con.execute('COPY (SELECT 1 AS arbitrary) TO ? (FORMAT PARQUET)', [str(source)])
    finally:
        con.close()
    with pytest.raises(ValueError, match='Missing required'):
        DailyActivityAggregator(source).run(tmp_path / 'out.parquet', tmp_path / 'report.json')
