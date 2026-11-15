"""Run from backend/: python3 scripts/build_fire_features.py"""
from pathlib import Path
import sys
BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))
from firescope.application.use_cases.build_fire_features import BuildFireFeatures

def main():
    report = BuildFireFeatures().execute(
        ROOT / 'data/processed/firescope_usa_fire_calendar.parquet',
        ROOT / 'data/processed/firescope_usa_fire_features.parquet',
        ROOT / 'reports/data_quality/fire_features_manifest.json',
    )
    for key in ('input_rows', 'output_rows', 'detections_preserved',
                'rows_with_prior_year_baseline_at_least_3',
                'rows_with_consecutive_previous_month', 'rows_with_historical_z_score'):
        print(f'{key}: {report[key]:,}')
    print(f"Output: {report['output']}")

if __name__ == '__main__':
    main()
