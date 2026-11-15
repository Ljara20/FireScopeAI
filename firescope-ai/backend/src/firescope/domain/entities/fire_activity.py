from dataclasses import dataclass
@dataclass(frozen=True)
class FireActivity:
    region_id: str
    year: int
    month: int
    observation_count: int
    # Raw observations are NOT a harmonized activity metric.
