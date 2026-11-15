"""Run from backend/: python scripts/normalize_observations.py"""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / 'src'))

from firescope.application.use_cases.normalize_observations import NormalizeObservations


def main() -> None:
    root = BACKEND.parent
    report = NormalizeObservations().execute(
        root / 'data/processed/firescope_usa_unified.parquet',
        root / 'data/processed/firescope_usa_normalized.parquet',
        root / 'reports/data_quality/normalization_manifest.json',
    )
    print('Normalized observations:', sum(x['observations'] for x in report['sensors']))
    print('Output:', report['output'])
    for row in report['sensors']:
        print(row)


if __name__ == '__main__':
    main()
