"""Application use case for daily sensor-specific fire activity aggregation."""
from pathlib import Path
from firescope.infrastructure.processing.daily_activity_aggregator import DailyActivityAggregator


class BuildDailyFireActivity:
    def __init__(self, aggregator_class=DailyActivityAggregator):
        self.aggregator_class = aggregator_class

    def execute(self, input_path: Path, output_path: Path, manifest_path: Path) -> dict:
        return self.aggregator_class(source=input_path).run(output_path, manifest_path)
