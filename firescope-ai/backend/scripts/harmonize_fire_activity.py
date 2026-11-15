"""Run Phase 2.5 from the backend directory."""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "src"))

from firescope.application.use_cases.harmonize_fire_activity import HarmonizeFireActivity


def main():
    root = BACKEND.parent
    report = HarmonizeFireActivity().execute(
        input_path=root / "data/processed/firescope_usa_daily_activity.parquet",
        output_path=root / "data/harmonized/firescope_usa_harmonized.parquet",
        manifest_path=root / "reports/data_quality/harmonization_manifest.json",
    )
    print(f"Input groups: {report['input_groups']:,}")
    print(f"Output groups: {report['output_groups']:,}")
    for sensor, info in report["sensor_results"].items():
        print(f"{sensor}: approved={info['approved']}, scale={info['scale']}, reason={info['reason']}")
    print(f"Output: {report['output']}")


if __name__ == "__main__":
    main()
