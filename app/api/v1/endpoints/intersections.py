from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.intersection import Intersection
from app.models.traffic import TrafficLight
from pydantic import BaseModel

router = APIRouter()

class IntersectionCreate(BaseModel):
    area_id: int
    name: str
    code: str
    location: str

@router.post("/")
def create_intersection(intersection: IntersectionCreate, db: Session = Depends(get_db)):
    # Create intersection
    db_intersection = Intersection(**intersection.model_dump())
    db.add(db_intersection)
    db.commit()
    db.refresh(db_intersection)
    
    # Auto-create 4 traffic lights
    directions = ["North", "South", "East", "West"]
    for i, direction in enumerate(directions):
        # Sync North and South to GREEN, others to RED
        is_ns = direction in ["North", "South"]
        light = TrafficLight(
            intersection_id=db_intersection.id,
            direction=direction,
            status="GREEN" if is_ns else "RED",
            duration=60 if is_ns else 60 # Default duration
        )
        db.add(light)
    db.commit()
    
    return {"message": "Intersection created with 4 traffic lights", "id": db_intersection.id}

@router.post("/{intersection_id}/reset")
async def reset_intersection(
    intersection_id: int,
    db: Session = Depends(get_db)
):
    """
    Reset an intersection to automatic mode.
    """
    lights = db.query(TrafficLight).filter(TrafficLight.intersection_id == intersection_id).all()
    if not lights:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    from app.services.redis import get_redis
    from app.api.v1.endpoints.websocket import broadcast_state_update
    from datetime import datetime, timedelta, timezone
    
    redis = await get_redis()
    
    for light in lights:
        light.is_manual = False
        # Reset to default state if needed, or just let the cycle pick it up
        # We'll set North/South to GREEN and East/West to RED to restart clean
        if light.direction in ["North", "South"]:
            light.status = "GREEN"
        else:
            light.status = "RED"
            
        light.last_updated = datetime.now(timezone.utc)
        
        # Update Redis
        await redis.set(f"traffic_light:{light.id}:status", light.status)
        # Set a fresh end time
        end_time = (datetime.now(timezone.utc) + timedelta(seconds=light.duration)).timestamp()
        await redis.set(f"traffic_light:{light.id}:end_time", end_time)
        
        # Broadcast
        await broadcast_state_update(light.id, {
            "status": light.status,
            "end_time": end_time
        })
        
    db.commit()
    return {"message": "Intersection reset to automatic mode"}
