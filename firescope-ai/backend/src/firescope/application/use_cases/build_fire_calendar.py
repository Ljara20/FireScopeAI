"""Use case: build a sensor-preserving historical activity calendar."""
from pathlib import Path
from typing import Any

from firescope.infrastructure.processing.fire_calendar_builder import FireCalendarBuilder


class BuildFireCalendar:
    def __init__(self, builder_class=FireCalendarBuilder):
        self.builder_class = builder_class

    def execute(self, input_path: Path, output_path: Path,
                climatology_path: Path, manifest_path: Path) -> dict[str, Any]:
        builder = self.builder_class(source=input_path)
        return builder.run(output_path, climatology_path, manifest_path)
