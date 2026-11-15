"""Planned ML component; no model has been trained."""
from firescope.shared.exceptions import NotImplementedStageError
class HistoricalBaseline:
    def run(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedStageError("HistoricalBaseline is not implemented in Data Foundation")
