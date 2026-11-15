"""Run from backend/: python3 scripts/validate_fire_forecasts.py"""
from pathlib import Path
import sys
BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))
from firescope.application.use_cases.validate_fire_forecasts import ValidateFireForecasts


def main():
    report = ValidateFireForecasts().execute(
        ROOT / 'data/processed/firescope_usa_fire_features.parquet',
        ROOT / 'data/processed/firescope_usa_fire_forecast_validation.parquet',
        ROOT / 'reports/data_quality/fire_forecast_validation_manifest.json')
    print(f"Rows: {report['input_rows']:,} -> {report['output_rows']:,}")
    print(f"Detections preserved: {report['detections_preserved']:,}")
    print(f"Independent test predictions: {report['independent_test_predictions']:,}")
    for sensor, stats in report['sensor_results'].items():
        print(f"{sensor}: selected={stats['selected_method']}, test={stats.get('independent_test')}")
    print(f"Output: {report['output']}")


if __name__ == '__main__':
    main()
