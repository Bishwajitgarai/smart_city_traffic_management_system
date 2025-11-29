from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TrafficLightBase(BaseModel):
    location: str
    status: str = "RED"
    is_active: bool = True

class TrafficLightCreate(TrafficLightBase):
    pass

class TrafficLightUpdate(BaseModel):
    location: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class TrafficLightResponse(TrafficLightBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
