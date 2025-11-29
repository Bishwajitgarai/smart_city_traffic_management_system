from pydantic import BaseModel
from typing import List
from app.schemas.traffic import TrafficLightResponse

class IntersectionResponseNested(BaseModel):
    id: int
    name: str
    code: str
    location: str
    traffic_lights: List[TrafficLightResponse] = []

    class Config:
        from_attributes = True
