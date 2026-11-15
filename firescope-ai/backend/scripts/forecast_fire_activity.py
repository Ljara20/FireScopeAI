"""Run from backend/: python3 scripts/forecast_fire_activity.py"""
from pathlib import Path
import sys
BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))
from firescope.application.use_cases.forecast_fire_activity import ForecastFireActivity

def main():
    report = ForecastFireActivity().execute(
        ROOT / 'data/processed/firescope_usa_fire_features.parquet',
        ROOT / 'data/processed/firescope_usa_fire_forecasts.parquet',
        ROOT / 'reports/data_quality/fire_forecasts_manifest.json',
    )
    print(f"Input rows: {report['input_rows']:,}")
    print(f"Output rows: {report['output_rows']:,}")
    print(f"Detections preserved: {report['detections_preserved']:,}")
    print(f"Forecast rows: {report['forecast_rows']:,}")
    for sensor, stats in report['sensor_results'].items():
        print(f'{sensor}: {stats}')
    print(f"Output: {report['output']}")

if __name__ == '__main__':
    main()
