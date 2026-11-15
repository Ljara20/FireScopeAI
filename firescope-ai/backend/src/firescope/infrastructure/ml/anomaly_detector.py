"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class AnomalyDetector:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("AnomalyDetector is not implemented in Data Foundation")
