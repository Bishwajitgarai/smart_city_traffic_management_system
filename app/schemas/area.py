from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.intersection import IntersectionResponseNested

class AreaBase(BaseModel):
    name: str
    code: str
    city_id: int

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    city_id: Optional[int] = None

class AreaResponse(AreaBase):
    id: int

    class Config:
        from_attributes = True

class AreaResponseNested(AreaBase):
    id: int
    intersections: List['IntersectionResponseNested'] = []

    class Config:
        from_attributes = True

# Avoid circular import
from app.schemas.intersection import IntersectionResponseNested
AreaResponseNested.model_rebuild()
