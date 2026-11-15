"""Retrospective experimental model evaluation endpoint."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from firescope.infrastructure.persistence.duckdb_repository import DuckDbRepository
from firescope.presentation.api.dependencies import get_repository

router = APIRouter(tags=["forecasts"])

Sensor = Literal["modis", "viirs_snpp", "viirs_noaa20"]

ForecastStatus = Literal[
    "independent_test_prediction",
    "insufficient_features",
    "outside_test",
]


class ForecastRecord(BaseModel):
    state_code: str | None
    state_name: str | None
    sensor: Sensor
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    feature_month: date
    detection_count: int = Field(ge=0)
    independent_forecast_detection_count: float | None
    independent_forecast_status: ForecastStatus
    baseline_years: int = Field(ge=0)
    has_minimum_baseline: bool
    has_consecutive_previous_month: bool


class ForecastsResponse(BaseModel):
    schema_version: str
    data_source: str
    sensor: Sensor
    geography: str
    metric: str
    unit: str
    records: list[ForecastRecord]
    count: int
    limit: int
    offset: int
    limitations: list[str]


@router.get("/forecasts", response_model=ForecastsResponse)
def list_forecasts(
    sensor: Sensor,
    repository: Annotated[DuckDbRepository, Depends(get_repository)],
    state_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ForecastsResponse:
    normalized_state = state_code.upper() if state_code else None

    rows = repository.query(
        "forecast_validation",
        sensor=sensor,
        state_code=normalized_state,
        year=year,
        limit=limit,
        offset=offset,
    )

    records = [ForecastRecord(**row) for row in rows]

    return ForecastsResponse(
        schema_version="1.0.0",
        data_source="firescope_usa_fire_forecast_validation.parquet",
        sensor=sensor,
        geography="United States — state",
        metric="retrospective_detection_count_estimate",
        unit="satellite_detections",
        records=records,
        count=len(records),
        limit=limit,
        offset=offset,
        limitations=[
            "These are retrospective experimental model estimates, not future forecasts.",
            "Satellite detections are not individual wildfires.",
            "Estimates are available only for independent test observations.",
            "Missing estimates are represented as null, not zero.",
            "Sensor characteristics and coverage differ.",
            "Missing observation periods must not be interpreted as zero activity.",
        ],
    )
