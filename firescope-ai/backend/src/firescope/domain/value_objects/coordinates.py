from dataclasses import dataclass
@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float
    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ValueError("Invalid geographic coordinates")
