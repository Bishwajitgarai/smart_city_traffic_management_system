from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.city import TrafficArea
from app.schemas.area import AreaCreate, AreaResponse, AreaUpdate, AreaResponseNested

router = APIRouter()

@router.post("/", response_model=AreaResponse)
def create_area(area: AreaCreate, db: Session = Depends(get_db)):
    db_area = TrafficArea(**area.model_dump())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

@router.get("/", response_model=List[AreaResponse])
def read_areas(db: Session = Depends(get_db)):
    areas = db.query(TrafficArea).all()
    return areas

from app.schemas.area import AreaCreate, AreaResponse, AreaUpdate, AreaResponseNested
from sqlalchemy.orm import joinedload
from app.models.intersection import Intersection

@router.get("/{area_id}", response_model=AreaResponseNested)
def read_area(area_id: int, db: Session = Depends(get_db)):
    area = db.query(TrafficArea).options(
        joinedload(TrafficArea.intersections)
        .joinedload(Intersection.traffic_lights)
    ).filter(TrafficArea.id == area_id).first()
    
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return area

@router.put("/{area_id}", response_model=AreaResponse)
def update_area(area_id: int, area_update: AreaUpdate, db: Session = Depends(get_db)):
    db_area = db.query(TrafficArea).filter(TrafficArea.id == area_id).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    update_data = area_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_area, key, value)
    
    db.commit()
    db.refresh(db_area)
    return db_area

@router.delete("/{area_id}")
def delete_area(area_id: int, db: Session = Depends(get_db)):
    db_area = db.query(TrafficArea).filter(TrafficArea.id == area_id).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    db.delete(db_area)
    db.commit()
    return {"message": "Area deleted"}
