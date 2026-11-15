"""Historical geographic coverage endpoint."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from firescope.infrastructure.persistence.duckdb_repository import (
    DuckDbRepository,
)
from firescope.presentation.api.dependencies import get_repository

router = APIRouter(tags=["regions"])

Sensor = Literal["modis", "viirs_snpp", "viirs_noaa20"]


class Region(BaseModel):
    state_code: str
    state_name: str


class RegionsResponse(BaseModel):
    schema_version: str
    data_source: str
    sensor: Sensor
    geography: str
    regions: list[Region]
    count: int
    limitations: list[str]


@router.get("/regions", response_model=RegionsResponse)
def list_regions(
    sensor: Sensor,
    repository: Annotated[DuckDbRepository, Depends(get_repository)],
) -> RegionsResponse:
    """Return states represented in historical monthly observations."""
    regions = [
        Region(**row)
        for row in repository.list_regions(sensor=sensor)
    ]

    return RegionsResponse(
        schema_version="1.0.0",
        data_source="firescope_usa_fire_calendar.parquet",
        sensor=sensor,
        geography="United States — state",
        regions=regions,
        count=len(regions),
        limitations=[
            "Regions indicate historical satellite observations, not active fires.",
            "Sensor coverage and detection characteristics differ.",
            "Absence from this list does not establish absence of fires.",
        ],
    )
