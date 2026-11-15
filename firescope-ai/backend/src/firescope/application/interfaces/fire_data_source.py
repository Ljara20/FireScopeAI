from pathlib import Path
from typing import Protocol
class FireDataSource(Protocol):
    def discover(self, directory: Path) -> list[Path]: ...
