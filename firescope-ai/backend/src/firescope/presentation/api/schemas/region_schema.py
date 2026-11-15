from pydantic import BaseModel
class RegionSchema(BaseModel):
    id: str
    name: str
