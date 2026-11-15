from dataclasses import dataclass
from datetime import date
from firescope.domain.value_objects.risk_level import RiskLevel
@dataclass(frozen=True)
class RiskForecast:
    region_id: str
    issued_on: date
    horizon_days: int
    score: float
    level: RiskLevel
    calibrated_probability: bool = False
