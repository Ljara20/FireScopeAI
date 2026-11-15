"""Stream only USA country CSV members from FIRMS ZIPs to typed Parquet."""
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import duckdb
from firescope.domain.value_objects.sensor_type import SensorType
from firescope.infrastructure.data_sources.nasa_firms_reader import NasaFirmsReader
from firescope.infrastructure.processing.usa_filter import UsaFilter
from firescope.shared.exceptions import DatasetSchemaError

@dataclass(frozen=True)
class IngestionResult:
    sensor: str
    archives: int
    country_files: int
    rows: int
    output: str | None
    warnings: tuple[str, ...]

class IngestFireData:
    REQUIRED = {"latitude", "longitude", "acq_date"}
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection
        self.reader = NasaFirmsReader()

    def execute(self, sensor: SensorType, input_dir: Path, output_dir: Path) -> IngestionResult:
        archives = self.reader.discover(input_dir) if input_dir.exists() else []
        warnings: list[str] = []
        total = 0
        country_files = 0
        pieces: list[Path] = []
        output_dir.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="firescope_") as temporary:
            tmp = Path(temporary)
            for index, archive in enumerate(archives):
                with ZipFile(archive) as zf:
                    members = [m for m in self.reader.csv_members(archive)
                               if UsaFilter.matches_country_filename(m)]
                    if not members:
                        warnings.append(f"No USA CSV found in {archive.name}; inspect ZIP member names")
                    for member_index, member in enumerate(members):
                        country_files += 1
                        csv_path = tmp / f"input_{index}_{member_index}.csv"
                        with zf.open(member) as source, csv_path.open("wb") as target:
                            import shutil
                            shutil.copyfileobj(source, target)
                        # all_varchar avoids inconsistent inferred types across archives.
                        cols = self.connection.execute(
                            "DESCRIBE SELECT * FROM read_csv(?, header=true, all_varchar=true)",
                            [str(csv_path)]).fetchall()
                        column_names = {row[0].lower() for row in cols}
                        if not self.REQUIRED.issubset(column_names):
                            raise DatasetSchemaError(f"{archive.name}:{member} missing {self.REQUIRED-column_names}")
                        # Include all source fields and explicit provenance. Parquet columns may
                        # differ by sensor/year; union_by_name is used in the next stage.
                        piece = tmp / f"piece_{index}_{member_index}.parquet"
                        escaped = str(piece).replace("'", "''")
                        self.connection.execute(f"""
                            COPY (
                              SELECT *, ?::VARCHAR AS source_sensor,
                                     ?::VARCHAR AS source_archive,
                                     ?::VARCHAR AS source_member
                              FROM read_csv(?, header=true, all_varchar=true)
                              WHERE TRY_CAST(latitude AS DOUBLE) BETWEEN -90 AND 90
                                AND TRY_CAST(longitude AS DOUBLE) BETWEEN -180 AND 180
                                AND TRY_CAST(acq_date AS DATE) IS NOT NULL
                            ) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)
                        """, [sensor.value, archive.name, member, str(csv_path)])
                        count = self.connection.execute(
                            "SELECT count(*) FROM read_parquet(?)", [str(piece)]).fetchone()[0]
                        total += count
                        pieces.append(piece)
                        csv_path.unlink()
            if not pieces:
                return IngestionResult(sensor.value, len(archives), 0, 0, None, tuple(warnings))
            output = output_dir / f"{sensor.value}_usa.parquet"
            escaped = str(output).replace("'", "''")
            self.connection.execute(f"""
                COPY (SELECT * FROM read_parquet(?, union_by_name=true))
                TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """, [[str(p) for p in pieces]])
        return IngestionResult(sensor.value, len(archives), country_files, total,
                               str(output), tuple(warnings))
