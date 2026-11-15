import json
import sys
from pathlib import Path
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from firescope.infrastructure.processing.model_readiness import ModelReadiness


def inputs(tmp_path):
    source, manifest = tmp_path / 'validation.parquet', tmp_path / 'manifest.json'
    rows = [dict(state_code='CA', sensor='modis', year=year, month=1,
                 detection_count=10, historical_mean=8.0,
                 independent_forecast_detection_count=9.0 if year == 2024 else None,
                 independent_forecast_status='independent_test_prediction' if year == 2024 else 'outside_test')
            for year in (2021, 2024)]
    pq.write_table(pa.Table.from_pylist(rows), source)
    err = abs(__import__('math').log1p(10) - __import__('math').log1p(9))
    manifest.write_text(json.dumps(dict(output_rows=2, detections_preserved=20, independent_test_predictions=1,
        split={'train_before': 2022, 'selection_years': [2022, 2023], 'test_years': [2024, 2025]},
        sensor_results={'modis': {'selected_method': 'ridge_log1p', 'test_rows': 1,
                                   'independent_test': {'selected_log_mae': err}}})))
    return source, manifest, rows


def test_readiness_report_and_contract(tmp_path):
    source, manifest, _ = inputs(tmp_path)
    result = ModelReadiness(source, manifest).run(tmp_path / 'readiness.json')
    assert result['release_gate'] == 'historical_analytics_only'
    assert result['row_count'] == 2 and result['detections_preserved'] == 20
    assert result['sensor_results']['modis']['by_year']['2024']['rows'] == 1
    assert result['sensor_results']['modis']['by_year']['2025'] is None
    assert 'validated_future_forecast' in result['display_policy']['prohibited']


def test_reject_prediction_outside_holdout(tmp_path):
    source, manifest, rows = inputs(tmp_path)
    rows[0]['independent_forecast_detection_count'] = 9.0
    rows[0]['independent_forecast_status'] = 'independent_test_prediction'
    pq.write_table(pa.Table.from_pylist(rows), source)
    with pytest.raises(ValueError, match='outside independent test'):
        ModelReadiness(source, manifest).run(tmp_path / 'readiness.json')


def test_reject_manifest_mismatch(tmp_path):
    source, manifest, _ = inputs(tmp_path)
    data = json.loads(manifest.read_text())
    data['detections_preserved'] = 99
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='conservation mismatch'):
        ModelReadiness(source, manifest).run(tmp_path / 'readiness.json')


def test_reject_overwrite(tmp_path):
    source, manifest, _ = inputs(tmp_path)
    with pytest.raises(ValueError, match='Output must differ'):
        ModelReadiness(source, manifest).run(source)
