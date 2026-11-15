from pathlib import Path
import duckdb
class ParquetRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection
    def row_count(self, path: Path) -> int:
        return self.connection.execute("SELECT count(*) FROM read_parquet(?)", [str(path)]).fetchone()[0]
