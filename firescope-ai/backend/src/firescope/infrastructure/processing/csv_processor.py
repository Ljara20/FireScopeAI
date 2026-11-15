"""CSV parsing/typing helpers; no scientific harmonization."""
import csv
from pathlib import Path
class CsvProcessor:
    @staticmethod
    def header(path: Path) -> list[str]:
        with path.open(encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f))
