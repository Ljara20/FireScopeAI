"""Historical monthly satellite detection activity endpoint."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from firescope.infrastructure.persistence.duckdb_repository import (
    DuckDbRepository,
)
from firescope.presentation.api.dependencies import get_repository

router = APIRouter(tags=["calendar"])

Sensor = Literal["modis", "viirs_snpp", "viirs_noaa20"]


class CalendarRecord(BaseModel):
    state_code: str | None
    state_name: str | None
    sensor: Sensor
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    month_start: date
    days_with_detections: int = Field(ge=0, le=31)
    detection_count: int = Field(ge=0)
    valid_frp_count: int = Field(ge=0)
    invalid_frp_count: int = Field(ge=0)
    frp_sum_mw: float | None
    median_daily_cell_aligned_log_activity: float | None
    aligned_daily_cell_groups: int | None = Field(ge=0)
    alignment_status: str


class CalendarResponse(BaseModel):
    schema_version: str
    data_source: str
    sensor: Sensor
    geography: str
    metric: str
    unit: str
    records: list[CalendarRecord]
    count: int
    limit: int
    offset: int
    limitations: list[str]


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    sensor: Sensor,
    repository: Annotated[DuckDbRepository, Depends(get_repository)],
    state_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CalendarResponse:
    """Return historical monthly observations for one satellite sensor."""
    rows = repository.query(
        "calendar",
        sensor=sensor,
        state_code=state_code,
        year=year,
        limit=limit,
        offset=offset,
    )

    records = [CalendarRecord(**row) for row in rows]

    return CalendarResponse(
        schema_version="1.0.0",
        data_source="firescope_usa_fire_calendar.parquet",
        sensor=sensor,
        geography="United States — state",
        metric="satellite_hotspot_detections",
        unit="detections",
        records=records,
        count=len(records),
        limit=limit,
        offset=offset,
        limitations=[
            "Detection counts are satellite observations, not unique fires.",
            "MODIS and VIIRS measurements are not directly interchangeable.",
            "Missing months are not represented as zero detections.",
            "This endpoint does not provide operational wildfire warnings.",
        ],
    )
