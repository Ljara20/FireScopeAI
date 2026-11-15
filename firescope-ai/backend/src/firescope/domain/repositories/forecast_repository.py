from typing import Protocol
from firescope.domain.entities.risk_forecast import RiskForecast
class ForecastRepository(Protocol):
    def save(self, forecast: RiskForecast) -> None: ...
