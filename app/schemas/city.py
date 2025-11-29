from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.area import AreaResponseNested

class CityBase(BaseModel):
    name: str
    code: str

class CityCreate(CityBase):
    pass

class CityUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class CityResponse(CityBase):
    id: int
    areas: List['AreaResponse'] = []

    class Config:
        from_attributes = True

# Avoid circular import
from app.schemas.area import AreaResponse
CityResponse.model_rebuild()
