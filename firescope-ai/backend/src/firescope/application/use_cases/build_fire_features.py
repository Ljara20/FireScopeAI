"""Use case for building historical, sensor-specific ML features."""
from pathlib import Path
from typing import Any
from firescope.infrastructure.processing.feature_engineer import FeatureEngineer

class BuildFireFeatures:
    def __init__(self, engineer_class=FeatureEngineer):
        self.engineer_class = engineer_class

    def execute(self, input_path: Path, output_path: Path, manifest_path: Path) -> dict[str, Any]:
        return self.engineer_class(input_path).run(output_path, manifest_path)
