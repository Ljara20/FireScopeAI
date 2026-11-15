"""Application entry point for Phase 3.5 readiness assessment."""
from pathlib import Path
from firescope.infrastructure.processing.model_readiness import ModelReadiness


class PrepareModelReadiness:
    def execute(self, source: Path, validation_manifest: Path, destination: Path) -> dict:
        return ModelReadiness(source, validation_manifest).run(destination)
