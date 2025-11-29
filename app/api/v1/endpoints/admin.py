from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.traffic_logic import TrafficController
from app.models.traffic import TrafficLight
from pydantic import BaseModel

router = APIRouter()

class ManualOverrideRequest(BaseModel):
    status: str
    duration: int = None

@router.post("/traffic-lights/{light_id}/manual")
async def manual_override(
    light_id: int, 
    request: ManualOverrideRequest,
    db: Session = Depends(get_db)
):
    controller = TrafficController(db)
    await controller.set_manual_state(light_id, request.status, request.duration)
    return {"message": "Manual override applied"}

@router.delete("/traffic-lights/{light_id}/manual")
async def reset_manual_override(
    light_id: int,
    db: Session = Depends(get_db)
):
    controller = TrafficController(db)
    await controller.reset_manual_state(light_id)
    return {"message": "Manual override reset"}

@router.put("/traffic-lights/{light_id}/duration")
async def update_duration(
    light_id: int, 
    duration: int,
    db: Session = Depends(get_db)
):
    light = db.query(TrafficLight).filter(TrafficLight.id == light_id).first()
    if not light:
        raise HTTPException(status_code=404, detail="Light not found")
    
    light.duration = duration
    db.commit()
    return {"message": "Duration updated"}
