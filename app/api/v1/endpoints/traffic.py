from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.traffic import TrafficLight
from app.schemas.traffic import TrafficLightCreate, TrafficLightResponse, TrafficLightUpdate
from app.services.redis import get_redis

router = APIRouter()

@router.post("/", response_model=TrafficLightResponse)
def create_traffic_light(
    traffic_light: TrafficLightCreate, 
    db: Session = Depends(get_db)
):
    db_traffic_light = TrafficLight(**traffic_light.model_dump())
    db.add(db_traffic_light)
    db.commit()
    db.refresh(db_traffic_light)
    return db_traffic_light

@router.get("/", response_model=List[TrafficLightResponse])
def read_traffic_lights(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    traffic_lights = db.query(TrafficLight).offset(skip).limit(limit).all()
    return traffic_lights

@router.get("/{traffic_light_id}", response_model=TrafficLightResponse)
def read_traffic_light(
    traffic_light_id: int, 
    db: Session = Depends(get_db)
):
    traffic_light = db.query(TrafficLight).filter(TrafficLight.id == traffic_light_id).first()
    if traffic_light is None:
        raise HTTPException(status_code=404, detail="Traffic light not found")
    return traffic_light

@router.put("/{traffic_light_id}", response_model=TrafficLightResponse)
async def update_traffic_light(
    traffic_light_id: int, 
    traffic_light_update: TrafficLightUpdate, 
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    db_traffic_light = db.query(TrafficLight).filter(TrafficLight.id == traffic_light_id).first()
    if db_traffic_light is None:
        raise HTTPException(status_code=404, detail="Traffic light not found")
    
    update_data = traffic_light_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_traffic_light, key, value)
    
    db.commit()
    db.refresh(db_traffic_light)

    # Cache status in Redis if updated
    if "status" in update_data:
        await redis.set(f"traffic_light:{traffic_light_id}:status", update_data["status"])

    return db_traffic_light
