from pathlib import Path
import sys
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from firescope.infrastructure.processing.fire_activity_forecaster import FireActivityForecaster


def sample(path):
    rows = []
    for sensor in ('modis', 'viirs_snpp'):
        for year in range(2015, 2026):
            for month in range(1, 13):
                rows.append(dict(state_code='CA', sensor=sensor, year=year, month=month,
                    detection_count=20 + month + (year - 2015),
                    lag_1_month_detections=20 + (month - 1 if month > 1 else 12) + (year - 2015),
                    historical_mean=float(20 + month), baseline_years=year - 2015,
                    month_sin=float(np.sin(2 * np.pi * month / 12)),
                    month_cos=float(np.cos(2 * np.pi * month / 12)),
                    has_consecutive_previous_month=True))
    pq.write_table(pa.Table.from_pylist(rows), path)


def test_forecast_preserves_rows_and_has_no_training_predictions(tmp_path):
    source, output, manifest = (tmp_path / name for name in ('input.parquet', 'output.parquet', 'manifest.json'))
    sample(source)
    report = FireActivityForecaster(source).run(output, manifest)
    rows = pq.read_table(output).to_pylist()
    assert report['input_rows'] == report['output_rows'] == 264
    assert report['detections_preserved'] == sum(r['detection_count'] for r in rows)
    assert all(r['forecast_detection_count'] is None for r in rows if r['year'] < 2024)
    assert all(r['forecast_detection_count'] is not None for r in rows if r['year'] >= 2024)
    assert set(report['sensor_results']) == {'modis', 'viirs_snpp'}


def test_missing_columns(tmp_path):
    source = tmp_path / 'input.parquet'
    pq.write_table(pa.table({'arbitrary': [1]}), source)
    with pytest.raises(ValueError, match='Missing required columns'):
        FireActivityForecaster(source).run(tmp_path / 'output.parquet', tmp_path / 'manifest.json')


def test_prevent_input_overwrite(tmp_path):
    source = tmp_path / 'input.parquet'
    sample(source)
    with pytest.raises(ValueError, match='must differ'):
        FireActivityForecaster(source).run(source, tmp_path / 'manifest.json')
