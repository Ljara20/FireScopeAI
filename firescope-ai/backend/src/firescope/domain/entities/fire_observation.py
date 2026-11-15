from dataclasses import dataclass
from datetime import date
from firescope.domain.value_objects.coordinates import Coordinates
from firescope.domain.value_objects.sensor_type import SensorType
@dataclass(frozen=True)
class FireObservation:
    location: Coordinates
    acquired_on: date
    sensor: SensorType
    frp_mw: float | None = None
    source_file: str = ""
