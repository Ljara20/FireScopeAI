from dataclasses import dataclass
from pathlib import Path
@dataclass(frozen=True)
class Settings:
    data_dir: Path
    @classmethod
    def from_project(cls, project_root: Path) -> "Settings":
        return cls(data_dir=project_root / "data")
