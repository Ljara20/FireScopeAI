from pathlib import Path

import duckdb
import pytest

from firescope.infrastructure.processing.fire_calendar_builder import FireCalendarBuilder


def _make_data(path: Path):
    con = duckdb.connect()
    try:
        con.execute("""
            CREATE TABLE x (
                activity_date DATE, sensor VARCHAR, state_code VARCHAR, state_name VARCHAR,
                detection_count BIGINT, valid_frp_count BIGINT, invalid_frp_count BIGINT,
                frp_sum_mw DOUBLE, aligned_log_activity DOUBLE, alignment_status VARCHAR
            )
        """)
        con.execute("""
            INSERT INTO x VALUES
            ('2024-07-01','modis','CA','California',2,2,0,10.0,1.1,'reference'),
            ('2024-07-02','modis','CA','California',3,2,1,8.0,1.2,'reference'),
            ('2024-07-01','viirs_snpp','CA','California',4,4,0,12.0,0.8,'validated_exploratory'),
            ('2025-07-01','modis','CA','California',1,1,0,2.0,0.7,'reference'),
            ('2025-08-01','modis',NULL,NULL,2,2,0,4.0,0.9,'reference')
        """)
        escaped = str(path).replace("'", "''")
        con.execute(f"COPY x TO '{escaped}' (FORMAT PARQUET)")
    finally:
        con.close()


def test_calendar_preserves_counts_and_sensors(tmp_path):
    src = tmp_path / 'input.parquet'
    dest = tmp_path / 'calendar.parquet'
    clim = tmp_path / 'climatology.parquet'
    manifest = tmp_path / 'manifest.json'
    _make_data(src)
    report = FireCalendarBuilder(src).run(dest, clim, manifest)
    assert report['input_detections'] == report['calendar_detections'] == 12
    assert report['calendar_monthly_groups'] == 4
    assert report['unassigned_state_detections'] == 2
    con = duckdb.connect()
    try:
        rows = con.execute("SELECT sensor, year, month, detection_count, days_with_detections "
                           "FROM read_parquet(?) WHERE state_code='CA' ORDER BY sensor, year", [str(dest)]).fetchall()
        assert rows == [('modis', 2024, 7, 5, 2), ('modis', 2025, 7, 1, 1),
                        ('viirs_snpp', 2024, 7, 4, 1)]
        clim_rows = con.execute("SELECT years_with_detections, mean_monthly_detection_count_observed_years "
                                "FROM read_parquet(?) WHERE state_code='CA' AND sensor='modis' AND month=7",
                                [str(clim)]).fetchall()
        assert clim_rows == [(2, 3.0)]
    finally:
        con.close()


def test_prevent_overwrite(tmp_path):
    src = tmp_path / 'input.parquet'
    _make_data(src)
    with pytest.raises(ValueError):
        FireCalendarBuilder(src).run(src, tmp_path / 'clim.parquet', tmp_path / 'manifest.json')


def test_missing_columns(tmp_path):
    src = tmp_path / 'bad.parquet'
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE x (sensor VARCHAR)")
        con.execute(f"COPY x TO '{str(src)}' (FORMAT PARQUET)")
    finally:
        con.close()
    with pytest.raises(ValueError, match='Missing required columns'):
        FireCalendarBuilder(src).run(tmp_path / 'out.parquet', tmp_path / 'clim.parquet', tmp_path / 'm.json')
