"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class Explainability:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("Explainability is not implemented in Data Foundation")
