"""Run from backend/: python3 scripts/prepare_model_readiness.py"""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))
from firescope.application.use_cases.prepare_model_readiness import PrepareModelReadiness


def main():
    report = PrepareModelReadiness().execute(
        ROOT / 'data/processed/firescope_usa_fire_forecast_validation.parquet',
        ROOT / 'reports/data_quality/fire_forecast_validation_manifest.json',
        ROOT / 'reports/data_quality/model_readiness_manifest.json',
    )
    print(f"Rows: {report['row_count']:,}; detections: {report['detections_preserved']:,}")
    print(f"Independent test predictions: {report['independent_test_predictions']:,}")
    for sensor, result in report['sensor_results'].items():
        print(f"{sensor}: {result['selection_method']}, test improvement={result['independent_test']['relative_improvement']:.2%}")
    print(f"Release gate: {report['release_gate']}")
    print('Output: reports/data_quality/model_readiness_manifest.json')


if __name__ == '__main__':
    main()
