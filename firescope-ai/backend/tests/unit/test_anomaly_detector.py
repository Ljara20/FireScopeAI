from pathlib import Path
import sys
import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from firescope.infrastructure.processing.anomaly_detector import AnomalyDetector


def fixture(tmp_path):
    source = tmp_path / 'features.parquet'
    con = duckdb.connect()
    try:
        con.execute(f"""COPY (
            SELECT * FROM (VALUES
                ('CA','California','modis',2020,1,100,3,10.0,10.0,9.0,TRUE),
                ('CA','California','modis',2021,1,30,4,10.0,10.0,2.0,TRUE),
                ('CA','California','modis',2022,1,10,5,10.0,10.0,0.0,TRUE),
                ('CA','California','modis',2023,1,0,6,50.0,10.0,-5.0,TRUE),
                ('CA','California','viirs_snpp',2020,1,20,2,10.0,10.0,1.0,FALSE),
                ('CA','California','viirs_snpp',2021,1,20,3,20.0,0.0,NULL,TRUE)
            ) AS t(state_code,state_name,sensor,year,month,detection_count,
                baseline_years,historical_mean,historical_std,historical_z_score,
                has_minimum_baseline)
        ) TO {AnomalyDetector.quote(source)} (FORMAT PARQUET)""")
    finally:
        con.close()
    return source


def test_classifies_and_preserves_counts(tmp_path):
    source = fixture(tmp_path)
    report = AnomalyDetector(source).run(tmp_path/'anomalies.parquet', tmp_path/'manifest.json')
    assert report['input_rows'] == report['output_rows'] == 6
    assert report['detections_preserved'] == 180
    assert report['anomaly_classes'] == {'extreme_high':1,'high':1,'typical':1,
                                          'extreme_low':1,'insufficient_baseline':2}
    con = duckdb.connect()
    try:
        results = con.execute(f'SELECT sensor, year, anomaly_class FROM read_parquet({AnomalyDetector.quote(tmp_path/"anomalies.parquet")})').fetchall()
        assert ('viirs_snpp', 2021, 'insufficient_baseline') in results
    finally:
        con.close()


def test_missing_columns(tmp_path):
    source = tmp_path/'bad.parquet'
    con = duckdb.connect()
    try:
        con.execute(f'COPY (SELECT 1 AS arbitrary) TO {AnomalyDetector.quote(source)} (FORMAT PARQUET)')
    finally:
        con.close()
    with pytest.raises(ValueError, match='Missing required columns'):
        AnomalyDetector(source).run(tmp_path/'out.parquet', tmp_path/'manifest.json')


def test_prevent_overwrite(tmp_path):
    source = fixture(tmp_path)
    with pytest.raises(ValueError, match='must differ'):
        AnomalyDetector(source).run(source, tmp_path/'manifest.json')
