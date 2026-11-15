from pathlib import Path
import duckdb
class DuckDbRepository:
    def __init__(self, database: Path | None = None):
        self.connection = duckdb.connect(str(database) if database else ":memory:")
    def close(self) -> None:
        self.connection.close()
