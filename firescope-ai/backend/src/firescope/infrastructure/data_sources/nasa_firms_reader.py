"""Discover FIRMS CSVs inside ZIP archives without extracting the entire archive."""
from pathlib import Path
from zipfile import ZipFile
class NasaFirmsReader:
    def discover(self, directory: Path) -> list[Path]:
        return sorted(p for p in directory.rglob("*.zip") if p.is_file())
    def csv_members(self, archive: Path) -> list[str]:
        with ZipFile(archive) as zf:
            return [m for m in zf.namelist() if m.lower().endswith(".csv") and not m.endswith("/")]
    def usa_members(self, archive: Path) -> list[str]:
        from firescope.infrastructure.processing.usa_filter import UsaFilter
        return [member for member in self.csv_members(archive)
                if UsaFilter.matches_country_filename(member)]
