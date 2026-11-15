import csv
from pathlib import Path
from zipfile import ZipFile
import duckdb
from firescope.application.use_cases.ingest_fire_data import IngestFireData
from firescope.domain.value_objects.sensor_type import SensorType

def test_zip_usa_ingestion(tmp_path: Path) -> None:
    raw = tmp_path / "modis"
    raw.mkdir()
    archive = raw / "modis_2018_all_countries.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("modis/2018/United_States.csv", "latitude,longitude,acq_date,frp\n34,-118,2018-01-01,12\n")
        zf.writestr("modis/2018/Canada.csv", "latitude,longitude,acq_date,frp\n50,-100,2018-01-01,3\n")
    con = duckdb.connect()
    result = IngestFireData(con).execute(SensorType.MODIS, raw, tmp_path / "processed")
    assert result.rows == 1
    assert result.country_files == 1
    assert con.execute("SELECT source_sensor FROM read_parquet(?)", [result.output]).fetchone()[0] == "modis"
    con.close()
