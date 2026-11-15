import pytest
from firescope.domain.value_objects.coordinates import Coordinates

def test_coordinates() -> None:
    assert Coordinates(40.0, -120.0).longitude == -120.0
    with pytest.raises(ValueError):
        Coordinates(91.0, 0.0)
