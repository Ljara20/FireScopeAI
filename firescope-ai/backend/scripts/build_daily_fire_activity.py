"""Run phase 2.4 from backend/: python3 scripts/build_daily_fire_activity.py"""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
PROJECT = BACKEND.parent
sys.path.insert(0, str(BACKEND / "src"))

from firescope.application.use_cases.build_daily_fire_activity import BuildDailyFireActivity


def main() -> None:
    source = PROJECT / "data/processed/firescope_usa_georeferenced.parquet"
    destination = PROJECT / "data/processed/firescope_usa_daily_activity.parquet"
    manifest = PROJECT / "reports/data_quality/daily_activity_manifest.json"
    result = BuildDailyFireActivity().execute(source, destination, manifest)
    print(f"Source observations: {result['source_observations']:,}")
    print(f"Aggregated observations: {result['aggregated_observations']:,}")
    print(f"Daily groups: {result['daily_groups']:,}")
    print(f"Without H3: {result['observations_without_h3']:,}")
    print(f"Output: {destination}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
