"""Application boundary for exploratory cross-sensor alignment."""
from pathlib import Path

from firescope.infrastructure.processing.sensor_harmonization import SensorHarmonizer


class HarmonizeFireActivity:
    def __init__(self, harmonizer_class=SensorHarmonizer):
        self.harmonizer_class = harmonizer_class

    def execute(self, input_path: Path, output_path: Path, manifest_path: Path,
                min_pairs: int = 100, min_years: int = 3):
        harmonizer = self.harmonizer_class(
            source=input_path, min_pairs=min_pairs, min_years=min_years
        )
        return harmonizer.run(output_path, manifest_path)
