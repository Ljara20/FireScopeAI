from fastapi import FastAPI
from firescope.presentation.api.routers import regions, calendar, forecasts, preparedness
app = FastAPI(title="FireScope AI", version="0.1.0", description="Stage 1: Data Foundation")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "data_foundation"}
for router in (regions.router, calendar.router, forecasts.router, preparedness.router):
    app.include_router(router, prefix="/api/v1")
