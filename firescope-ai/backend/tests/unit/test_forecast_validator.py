from pathlib import Path
import sys
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from firescope.infrastructure.processing.forecast_validator import ForecastValidator


def fixture(path):
    rows = []
    for sensor in ('modis', 'viirs_snpp'):
        for state in ('CA', 'TX', 'OR'):
            for year in range(2015, 2026):
                for month in range(1, 13):
                    rows.append(dict(state_code=state, sensor=sensor, year=year, month=month,
                                     detection_count=20 + (month % 5) + (year % 3),
                                     lag_1_month_detections=20.0,
                                     historical_mean=22.0, baseline_years=4,
                                     month_sin=0.0, month_cos=1.0,
                                     has_consecutive_previous_month=True))
    pq.write_table(pa.Table.from_pylist(rows), path)
    return len(rows), sum(r['detection_count'] for r in rows)


def test_independent_validation_preserves_rows_and_splits(tmp_path):
    source, dest, manifest = (tmp_path / x for x in ('input.parquet', 'out.parquet', 'report.json'))
    count, detections = fixture(source)
    report = ForecastValidator(source).run(dest, manifest)
    assert report['input_rows'] == report['output_rows'] == count
    assert report['detections_preserved'] == detections
    assert report['independent_test_predictions'] == 2 * 3 * 2 * 12
    assert report['split']['selection_years'] == [2022, 2023]
    assert report['split']['test_years'] == [2024, 2025]
    assert all(x['selection_rows'] == 72 and x['test_rows'] == 72 for x in report['sensor_results'].values())
    out = pq.read_table(dest).to_pylist()
    assert all(r['independent_forecast_detection_count'] is None for r in out if r['year'] < 2024)
    assert all(r['independent_forecast_detection_count'] is not None for r in out if r['year'] >= 2024)


def test_missing_columns(tmp_path):
    source = tmp_path / 'in.parquet'
    pq.write_table(pa.table({'year': [2020]}), source)
    with pytest.raises(ValueError, match='Missing required columns'):
        ForecastValidator(source).run(tmp_path / 'out.parquet', tmp_path / 'report.json')


def test_prevent_input_overwrite(tmp_path):
    source = tmp_path / 'in.parquet'
    fixture(source)
    with pytest.raises(ValueError, match='paths must differ'):
        ForecastValidator(source).run(source, tmp_path / 'report.json')
