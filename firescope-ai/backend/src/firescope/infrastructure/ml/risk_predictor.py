"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class RiskPredictor:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("RiskPredictor is not implemented in Data Foundation")
