"""Small synthetic dataset tests; no NASA download needed."""
import csv
import json
from pathlib import Path
import duckdb
import pytest
from firescope.application.use_cases.assess_data_quality import AssessDataQuality
from firescope.infrastructure.processing.data_quality import FireDataQualityProfiler


def test_quality_reports(tmp_path: Path):
    source = tmp_path / 'sample.parquet'
    con = duckdb.connect()
    con.execute(f"""COPY (
      SELECT * FROM (VALUES
        ('modis', '38.5', '-120.1', '2020-07-01', '12.5', '70', '1200', 'Terra', 'MODIS', 'D'),
        ('modis', '38.5', '-120.1', '2020-07-01', '12.5', '70', '1200', 'Terra', 'MODIS', 'D'),
        ('viirs_snpp', '999', '-120', 'bad-date', '-1', 'n', '1200', 'N', 'VIIRS', 'N')
      ) AS t(source_sensor,latitude,longitude,acq_date,frp,confidence,acq_time,satellite,instrument,daynight)
    ) TO '{source}' (FORMAT PARQUET)""")
    con.close()
    output = tmp_path / 'reports'
    result = AssessDataQuality(FireDataQualityProfiler(source)).execute(output)
    assert result['total_observations'] == 3
    with (output / 'sensor_quality.csv').open() as f:
        records = {row['sensor']: row for row in csv.DictReader(f)}
    assert records['viirs_snpp']['invalid_coordinates'] == '1'
    assert records['viirs_snpp']['invalid_dates'] == '1'
    assert records['viirs_snpp']['invalid_frp'] == '1'
    with (output / 'potential_duplicates.csv').open() as f:
        duplicates = list(csv.DictReader(f))
    assert duplicates[0]['extra_rows_in_duplicate_groups'] == '1'
    assert json.loads((output / 'quality_manifest.json').read_text())['total_observations'] == 3


def test_missing_columns(tmp_path: Path):
    source = tmp_path / 'bad.parquet'
    con = duckdb.connect()
    con.execute(f"COPY (SELECT 1 AS latitude) TO '{source}' (FORMAT PARQUET)")
    con.close()
    with pytest.raises(ValueError, match='Missing required columns'):
        FireDataQualityProfiler(source).run(tmp_path / 'out')
