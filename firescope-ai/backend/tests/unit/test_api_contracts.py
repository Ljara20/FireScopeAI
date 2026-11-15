"""Scientific API response contract tests."""

from datetime import date

import pytest
from pydantic import ValidationError

from firescope.presentation.api.routers.calendar import CalendarRecord
from firescope.presentation.api.routers.regions import Region


def valid_calendar_record() -> dict:
    return {
        "state_code": "CA",
        "state_name": "California",
        "sensor": "modis",
        "year": 2024,
        "month": 7,
        "month_start": date(2024, 7, 1),
        "days_with_detections": 15,
        "detection_count": 100,
        "valid_frp_count": 90,
        "invalid_frp_count": 10,
        "frp_sum_mw": 500.0,
        "median_daily_cell_aligned_log_activity": None,
        "aligned_daily_cell_groups": None,
        "alignment_status": "unavailable",
    }


def test_calendar_accepts_valid_record() -> None:
    record = CalendarRecord(**valid_calendar_record())

    assert record.detection_count == 100
    assert record.sensor == "modis"


def test_calendar_preserves_null_values() -> None:
    record = CalendarRecord(**valid_calendar_record())

    payload = record.model_dump(mode="json")

    assert payload["median_daily_cell_aligned_log_activity"] is None
    assert payload["aligned_daily_cell_groups"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("detection_count", -1),
        ("valid_frp_count", -1),
        ("invalid_frp_count", -1),
        ("days_with_detections", -1),
        ("days_with_detections", 32),
        ("month", 0),
        ("month", 13),
        ("year", 1900),
        ("aligned_daily_cell_groups", -1),
    ],
)
def test_calendar_rejects_invalid_values(
    field: str,
    value: int,
) -> None:
    data = valid_calendar_record()
    data[field] = value

    with pytest.raises(ValidationError):
        CalendarRecord(**data)


def test_calendar_rejects_unknown_sensor() -> None:
    data = valid_calendar_record()
    data["sensor"] = "unknown"

    with pytest.raises(ValidationError):
        CalendarRecord(**data)


def test_region_preserves_geography() -> None:
    region = Region(
        state_code="CA",
        state_name="California",
    )

    assert region.state_code == "CA"
    assert region.state_name == "California"
