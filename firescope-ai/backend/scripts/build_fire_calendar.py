"""Run from backend/: python3 scripts/build_fire_calendar.py"""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))

from firescope.application.use_cases.build_fire_calendar import BuildFireCalendar


def main() -> None:
    report = BuildFireCalendar().execute(
        input_path=ROOT / 'data/harmonized/firescope_usa_harmonized.parquet',
        output_path=ROOT / 'data/processed/firescope_usa_fire_calendar.parquet',
        climatology_path=ROOT / 'data/processed/firescope_usa_fire_climatology.parquet',
        manifest_path=ROOT / 'reports/data_quality/fire_calendar_manifest.json',
    )
    print(f"Input daily groups: {report['input_daily_groups']:,}")
    print(f"Monthly calendar groups: {report['calendar_monthly_groups']:,}")
    print(f"Climatology groups: {report['climatology_groups']:,}")
    print(f"Detections preserved: {report['calendar_detections']:,}")
    print(f"Calendar: {report['calendar_output']}")
    print(f"Climatology: {report['climatology_output']}")


if __name__ == '__main__':
    main()
