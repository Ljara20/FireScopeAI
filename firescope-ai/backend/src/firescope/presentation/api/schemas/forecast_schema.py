from pydantic import BaseModel, Field
class ForecastSchema(BaseModel):
    region_id: str
    horizon_days: int = Field(gt=0)
    score: float = Field(ge=0, le=100)
    calibrated_probability: bool = False
