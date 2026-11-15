from pathlib import Path

import duckdb
import pytest

from firescope.infrastructure.processing.sensor_harmonization import SensorHarmonizer


def make_source(path: Path):
    con = duckdb.connect()
    try:
        con.execute("""
            CREATE TABLE samples (
                activity_date DATE, sensor VARCHAR, h3_cell_id VARCHAR,
                detection_count INTEGER, state_code VARCHAR
            )
        """)
        rows = []
        for year in (2018, 2019, 2020, 2021, 2022):
            for month in (1, 2, 3, 4):
                for cell in range(8):
                    date = f"{year}-{month:02d}-01"
                    n = 10 + cell
                    rows.extend([(date, "modis", str(cell), n, "CA"),
                                 (date, "viirs_snpp", str(cell), n * 2, "CA")])
        con.executemany("INSERT INTO samples VALUES (?, ?, ?, ?, ?)", rows)
        con.execute(f"COPY samples TO '{str(path).replace(chr(39), chr(39)*2)}' (FORMAT PARQUET)")
    finally:
        con.close()


def test_harmonization_preserves_groups_and_validates(tmp_path):
    src, out, manifest = (tmp_path / name for name in ("input.parquet", "out.parquet", "report.json"))
    make_source(src)
    result = SensorHarmonizer(src, min_pairs=10).run(out, manifest)
    assert result["input_groups"] == result["output_groups"] == 320
    assert result["sensor_results"]["viirs_snpp"]["approved"]
    assert not result["sensor_results"]["viirs_noaa20"]["approved"]
    assert manifest.exists()
    con = duckdb.connect()
    assert con.execute(f"SELECT count(*) FROM read_parquet('{out}') WHERE aligned_log_activity IS NOT NULL").fetchone()[0] == 320
    con.close()


def test_missing_columns(tmp_path):
    src = tmp_path / "bad.parquet"
    con = duckdb.connect()
    con.execute(f"COPY (SELECT 1 AS a) TO '{src}' (FORMAT PARQUET)")
    con.close()
    with pytest.raises(ValueError, match="Missing required columns"):
        SensorHarmonizer(src).run(tmp_path / "out.parquet", tmp_path / "manifest.json")


def test_prevent_input_overwrite(tmp_path):
    src = tmp_path / "input.parquet"
    make_source(src)
    with pytest.raises(ValueError, match="overwrite"):
        SensorHarmonizer(src).run(src, tmp_path / "manifest.json")
