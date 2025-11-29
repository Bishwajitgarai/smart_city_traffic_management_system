from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TrafficLightBase(BaseModel):
    direction: str
    status: str = "RED"
    current_density: int = 0
    duration: int = 60
    is_manual: bool = False
    is_active: bool = True

class TrafficLightCreate(TrafficLightBase):
    intersection_id: int

class TrafficLightUpdate(BaseModel):
    direction: Optional[str] = None
    status: Optional[str] = None
    current_density: Optional[int] = None
    duration: Optional[int] = None
    is_manual: Optional[bool] = None
    is_active: Optional[bool] = None

class TrafficLightResponse(TrafficLightBase):
    id: int
    intersection_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True
