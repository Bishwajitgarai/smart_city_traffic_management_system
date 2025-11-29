from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.intersection import Intersection
from app.models.traffic import TrafficLight
from app.core.traffic_logic import TrafficController

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

from app.models.city import City

@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    cities = db.query(City).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "cities": cities})

@router.post("/simulate/{light_id}/density")
async def simulate_density(
    light_id: int, 
    value: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    controller = TrafficController(db)
    background_tasks.add_task(controller.update_density, light_id, value)
    return {"message": "Density update queued"}

@router.get("/sync")
async def sync_state(db: Session = Depends(get_db)):
    controller = TrafficController(db)
    # Ideally fetch only active lights or filter by area
    lights = db.query(TrafficLight).all()
    data = {}
    for light in lights:
        state = await controller.get_state(light.id)
        data[light.id] = state
    return data
