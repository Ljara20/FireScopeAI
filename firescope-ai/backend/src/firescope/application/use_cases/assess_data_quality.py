"""Application use case for generating reproducible quality reports."""
from __future__ import annotations
import json
from pathlib import Path
from firescope.infrastructure.processing.data_quality import FireDataQualityProfiler


class AssessDataQuality:
    def __init__(self, profiler: FireDataQualityProfiler):
        self._profiler = profiler

    def execute(self, output_dir: Path) -> dict:
        result = self._profiler.run(output_dir)
        (Path(output_dir) / 'quality_manifest.json').write_text(
            json.dumps(result, indent=2), encoding='utf-8'
        )
        return result
