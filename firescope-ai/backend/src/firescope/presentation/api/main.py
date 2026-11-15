"""FireScope AI REST API."""

from fastapi import FastAPI

from firescope.presentation.api.routers import (
    anomalies,
    calendar,
    forecasts,
    preparedness,
    regions,
)

app = FastAPI(
    title="FireScope AI API",
    version="0.1.0",
    description=(
        "Research API for historical MODIS and VIIRS satellite fire activity, "
        "climatology, retrospective anomalies, and experimental model evaluation. "
        "Not an operational wildfire early-warning system."
    ),
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return the API health status."""
    return {
        "status": "ok",
        "service": "firescope-api",
        "version": "0.1.0",
    }


for router in (
    regions.router,
    calendar.router,
    anomalies.router,
    forecasts.router,
    preparedness.router,
):
    app.include_router(router, prefix="/api/v1")