"""Application use case for retrospective monthly anomaly classification."""
from pathlib import Path
from typing import Any
from firescope.infrastructure.processing.anomaly_detector import AnomalyDetector

class DetectFireAnomalies:
    def __init__(self, detector_class=AnomalyDetector):
        self.detector_class = detector_class

    def execute(self, input_path: Path, output_path: Path, manifest_path: Path) -> dict[str, Any]:
        return self.detector_class(input_path).run(output_path, manifest_path)
