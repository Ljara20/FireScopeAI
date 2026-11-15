"""Application use case for retrospective sensor-specific forecasting."""
from pathlib import Path
from typing import Any
from firescope.infrastructure.processing.fire_activity_forecaster import FireActivityForecaster

class ForecastFireActivity:
    def __init__(self, forecaster_class=FireActivityForecaster):
        self.forecaster_class = forecaster_class

    def execute(self, input_path: Path, output_path: Path, manifest_path: Path) -> dict[str, Any]:
        return self.forecaster_class(input_path).run(output_path, manifest_path)
