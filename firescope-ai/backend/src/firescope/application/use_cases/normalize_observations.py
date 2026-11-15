"""Application use case for technical normalization."""
from pathlib import Path
from firescope.infrastructure.processing.observation_normalizer import ObservationNormalizer


class NormalizeObservations:
    def execute(self, input_path: Path, output_path: Path, report_path: Path) -> dict:
        return ObservationNormalizer(input_path).run(output_path, report_path)
