"""Historical seasonal activity context for preparedness."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from firescope.infrastructure.persistence.duckdb_repository import DuckDbRepository
from firescope.presentation.api.dependencies import get_repository

router = APIRouter(tags=["preparedness"])

Sensor = Literal["modis", "viirs_snpp", "viirs_noaa20"]


class PreparednessRecord(BaseModel):
    state_code: str | None
    state_name: str | None
    sensor: Sensor
    month: int = Field(ge=1, le=12)
    years_with_detections: int = Field(ge=1)
    mean_monthly_detection_count_observed_years: float
    median_monthly_detection_count_observed_years: float
    min_monthly_detection_count_observed_years: int
    max_monthly_detection_count_observed_years: int
    mean_days_with_detections_observed_years: float
    median_of_monthly_aligned_log_activity: float | None
    first_observed_year: int
    last_observed_year: int


class PreparednessResponse(BaseModel):
    schema_version: str
    data_source: str
    sensor: Sensor
    geography: str
    metric: str
    unit: str
    records: list[PreparednessRecord]
    count: int
    limit: int
    offset: int
    limitations: list[str]


@router.get("/preparedness", response_model=PreparednessResponse)
def list_preparedness(
    sensor: Sensor,
    repository: Annotated[DuckDbRepository, Depends(get_repository)],
    state_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PreparednessResponse:
    rows = repository.query(
        "climatology",
        sensor=sensor,
        state_code=state_code.upper() if state_code else None,
        limit=limit,
        offset=offset,
    )

    records = [PreparednessRecord(**row) for row in rows]

    return PreparednessResponse(
        schema_version="1.0.0",
        data_source="firescope_usa_fire_climatology.parquet",
        sensor=sensor,
        geography="United States — state",
        metric="historical_monthly_detection_activity",
        unit="satellite_detections",
        records=records,
        count=len(records),
        limit=limit,
        offset=offset,
        limitations=[
            "Historical satellite activity is not wildfire risk.",
            "Satellite detections are not individual wildfires.",
            "This endpoint does not provide operational alerts or predictions.",
            "Missing observation periods must not be interpreted as zero activity.",
            "Sensor coverage and detection characteristics differ.",
            "Monthly averages include observed years only.",
        ],
    )
