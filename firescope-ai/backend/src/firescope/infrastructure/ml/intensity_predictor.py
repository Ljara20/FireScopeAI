"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class IntensityPredictor:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("IntensityPredictor is not implemented in Data Foundation")
