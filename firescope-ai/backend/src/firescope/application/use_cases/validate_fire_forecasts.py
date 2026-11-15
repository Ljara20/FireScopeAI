from pathlib import Path
from firescope.infrastructure.processing.forecast_validator import ForecastValidator


class ValidateFireForecasts:
    def __init__(self, validator_class=ForecastValidator):
        self.validator_class = validator_class

    def execute(self, source: Path, destination: Path, manifest: Path):
        return self.validator_class(source).run(destination, manifest)
