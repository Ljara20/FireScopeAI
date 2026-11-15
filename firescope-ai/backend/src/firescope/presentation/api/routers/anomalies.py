"""Historical satellite detection anomaly endpoint."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from firescope.infrastructure.persistence.duckdb_repository import DuckDbRepository
from firescope.presentation.api.dependencies import get_repository

router = APIRouter(tags=["anomalies"])

Sensor = Literal["modis", "viirs_snpp", "viirs_noaa20"]


class AnomalyRecord(BaseModel):
    state_code: str
    state_name: str
    sensor: Sensor

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    feature_month: date

    detection_count: int = Field(ge=0)
    days_with_detections: int = Field(ge=0, le=31)

    frp_sum_mw: float | None
    median_daily_cell_aligned_log_activity: float | None
    alignment_status: str

    baseline_years: int = Field(ge=0)
    historical_mean: float | None
    historical_std: float | None
    historical_median: float | None
    historical_activity_ratio: float | None
    historical_z_score: float | None

    has_minimum_baseline: bool

    anomaly_class: Literal[
        "typical",
        "insufficient_baseline",
        "extreme_high",
        "high",
        "low",
        "extreme_low",
    ]

    anomaly_assessable: bool
    anomaly_method: str


class AnomaliesResponse(BaseModel):
    schema_version: str
    data_source: str
    sensor: Sensor
    geography: str
    metric: str
    unit: str

    records: list[AnomalyRecord]
    count: int
    limit: int
    offset: int

    limitations: list[str]


@router.get("/anomalies", response_model=AnomaliesResponse)
def list_anomalies(
    sensor: Sensor,
    repository: Annotated[DuckDbRepository, Depends(get_repository)],
    state_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnomaliesResponse:
    """Return historical anomalies for one satellite sensor."""

    normalized_state = state_code.upper() if state_code else None

    rows = repository.query(
        "anomalies",
        sensor=sensor,
        state_code=normalized_state,
        year=year,
        limit=limit,
        offset=offset,
    )

    records = [AnomalyRecord(**row) for row in rows]

    return AnomaliesResponse(
        schema_version="1.0.0",
        data_source="firescope_usa_fire_anomalies.parquet",
        sensor=sensor,
        geography="United States — state",
        metric="historical_detection_anomaly",
        unit="z_score",
        records=records,
        count=len(records),
        limit=limit,
        offset=offset,
        limitations=[
            "Satellite detections are not individual wildfires.",
            "Anomalies describe historical observations, not future predictions.",
            "Insufficient historical baseline prevents anomaly assessment.",
            "Sensor characteristics and coverage differ.",
            "Missing observation periods must not be interpreted as zero activity.",
        ],
    )