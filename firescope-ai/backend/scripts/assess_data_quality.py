"""CLI for FireScope AI Phase 2.1 quality assessment."""
from __future__ import annotations
import argparse
from pathlib import Path
from _bootstrap import DATA, REPORTS
from firescope.application.use_cases.assess_data_quality import AssessDataQuality
from firescope.infrastructure.processing.data_quality import FireDataQualityProfiler


def main() -> None:
    parser = argparse.ArgumentParser(description='Profile NASA FIRMS unified Parquet')
    parser.add_argument('--input', type=Path, default=DATA / 'processed' / 'firescope_usa_unified.parquet')
    parser.add_argument('--output', type=Path, default=REPORTS / 'data_quality')
    args = parser.parse_args()
    result = AssessDataQuality(FireDataQualityProfiler(args.input)).execute(args.output)
    print(f"Processed {result['total_observations']:,} observations")
    print(f'Reports: {args.output.resolve()}')
    for report in result['reports']:
        print(f'  {report}')
    print('  quality_manifest.json')


if __name__ == '__main__':
    main()
