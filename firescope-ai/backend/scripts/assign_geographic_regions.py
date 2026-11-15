"""Run from backend/: python3 scripts/assign_geographic_regions.py"""
import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "src"))

from firescope.application.use_cases.assign_geographic_regions import AssignGeographicRegions

def main():
    root = BACKEND.parent
    parser = argparse.ArgumentParser(description="Assign state polygons and H3 cells to normalized FIRMS observations")
    parser.add_argument("--states", type=Path, default=root / "data/reference/us_states.zip",
                        help="Census state boundaries ZIP/GeoJSON/Shapefile with STUSPS and NAME")
    parser.add_argument("--resolution", type=int, default=5, help="H3 resolution (0–15), default 5")
    parser.add_argument("--batch-size", type=int, default=50_000)
    args = parser.parse_args()
    result = AssignGeographicRegions().execute(
        root / "data/processed/firescope_usa_normalized.parquet",
        args.states,
        root / "data/processed/firescope_usa_georeferenced.parquet",
        root / "reports/data_quality/spatial_manifest.json",
        resolution=args.resolution,
        batch_size=args.batch_size,
    )
    print("Processed:", result["total_observations"])
    print("Spatial status:", result["spatial_status_counts"])
    print("Output:", result["output"])
    print("Manifest:", root / "reports/data_quality/spatial_manifest.json")


if __name__ == "__main__":
    main()
