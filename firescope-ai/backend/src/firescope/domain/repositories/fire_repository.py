from typing import Protocol
from firescope.domain.entities.fire_observation import FireObservation
class FireRepository(Protocol):
    def save(self, observations: list[FireObservation]) -> None: ...
