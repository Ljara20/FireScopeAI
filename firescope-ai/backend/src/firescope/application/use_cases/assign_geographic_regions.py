from pathlib import Path

from firescope.infrastructure.processing.spatial_processor import SpatialProcessor


class AssignGeographicRegions:
    """Caso de uso para asignar estados y celdas H3."""

    def __init__(self, processor_class=SpatialProcessor):
        self.processor_class = processor_class

    def execute(
        self,
        input_path: Path,
        states_path: Path,
        output_path: Path,
        manifest_path: Path,
        resolution: int = 5,
        batch_size: int = 50_000,
    ):
        processor = self.processor_class(
            source=input_path,
            states_file=states_path,
            resolution=resolution,
            batch_size=batch_size,
        )

        return processor.run(
            output_path,
            manifest_path,
        )