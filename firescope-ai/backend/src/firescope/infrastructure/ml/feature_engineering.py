"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class FeatureEngineering:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("FeatureEngineering is not implemented in Data Foundation")
