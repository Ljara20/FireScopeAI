"""Inventory ZIP archives and their USA country CSV members."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from _bootstrap import DATA, REPORTS
from firescope.infrastructure.processing.usa_filter import UsaFilter

SENSORS = {"modis": "modis", "viirs_snpp": "viirs_snpp", "viirs_noaa20": "viirs_noaa20"}
def inspect(raw: Path) -> dict:
    result = {}
    for sensor, folder in SENSORS.items():
        records = []
        for archive in sorted((raw / folder).rglob("*.zip")) if (raw / folder).exists() else []:
            try:
                with ZipFile(archive) as zf:
                    csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                    usa = [n for n in csvs if UsaFilter.matches_country_filename(n)]
                    records.append({"archive": archive.name, "size_mb": round(archive.stat().st_size/1048576, 2),
                                    "csv_count": len(csvs), "usa_members": usa,
                                    "example_members": csvs[:8] if not usa else []})
            except BadZipFile:
                records.append({"archive": archive.name, "error": "Invalid ZIP"})
        result[sensor] = records
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=DATA / "raw")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    result = inspect(args.raw)
    target = REPORTS / "archive_inventory.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for sensor, archives in result.items():
        print(f"{sensor}: {len(archives)} ZIPs, {sum(len(a.get('usa_members', [])) for a in archives)} USA files")
    print(f"Report: {target}")
if __name__ == "__main__":
    main()
