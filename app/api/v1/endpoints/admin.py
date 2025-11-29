from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.traffic_logic import TrafficController
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
