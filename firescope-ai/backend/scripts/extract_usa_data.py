"""Extract only USA CSV members from yearly FIRMS ZIPs into sensor Parquet files."""
import argparse
import json
from pathlib import Path
import duckdb
from _bootstrap import DATA, REPORTS
from firescope.application.use_cases.ingest_fire_data import IngestFireData
from firescope.domain.value_objects.sensor_type import SensorType

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=DATA / "raw")
    parser.add_argument("--output", type=Path, default=DATA / "processed")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    con = duckdb.connect()
    con.execute(f"SET threads={max(1, args.threads)}")
    con.execute("SET preserve_insertion_order=false")
    use_case = IngestFireData(con)
    results = []
    for sensor in SensorType:
        result = use_case.execute(sensor, args.raw / sensor.value, args.output)
        results.append(result.__dict__)
        print(f"{sensor.value}: {result.rows:,} rows / {result.country_files} USA files")
        for warning in result.warnings:
            print("WARNING:", warning)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "ingestion_report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    con.close()
if __name__ == "__main__":
    main()
