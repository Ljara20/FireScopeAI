from dataclasses import dataclass
@dataclass(frozen=True)
class GeographicRegion:
    region_id: str
    name: str
    country: str
