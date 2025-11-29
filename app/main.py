from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine, SessionLocal

from fastapi.staticfiles import StaticFiles
from app.models.city import City, TrafficArea
from app.models.intersection import Intersection
from app.models.traffic import TrafficLight
from fastapi.responses import RedirectResponse

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)

def seed_data():
    db = SessionLocal()
    if not db.query(City).first():
        # Create City
        city = City(name="Metropolis", code="MET")
        db.add(city)
        db.commit()
        db.refresh(city)

        # Create Areas
        downtown = TrafficArea(name="Downtown", code="DT", city_id=city.id)
        uptown = TrafficArea(name="Uptown", code="UP", city_id=city.id)
        db.add_all([downtown, uptown])
        db.commit()
        db.refresh(downtown)
        db.refresh(uptown)

        # Create Intersections
        intersections_data = [
            {"name": "Main St & 1st Ave", "code": "INT-001", "area_id": downtown.id, "location": "Downtown Core"},
            {"name": "Broadway & 5th", "code": "INT-002", "area_id": downtown.id, "location": "Financial District"},
            {"name": "Park Ave & 59th", "code": "INT-003", "area_id": uptown.id, "location": "Residential Zone"},
        ]

        for i_data in intersections_data:
            intersection = Intersection(**i_data)
            db.add(intersection)
            db.commit()
            db.refresh(intersection)
            
            # Create lights
            directions = ["North", "South", "East", "West"]
            for direction in directions:
                light = TrafficLight(
                    intersection_id=intersection.id,
                    direction=direction,
                    status="RED" if direction in ["East", "West"] else "GREEN",
                    duration=60
                )
                db.add(light)
            db.commit()
    db.close()

@app.on_event("startup")
async def startup_event():
    # Seed data
    seed_data()
    
    # Start background task
    import asyncio
    from app.core.traffic_logic import TrafficController
    from app.db.session import SessionLocal
    
    # We need to run this in the background
    loop = asyncio.get_running_loop()
    # Create a persistent session for the background task
    db = SessionLocal()
    controller = TrafficController(db)
    loop.create_task(controller.run_cycle())

@app.get("/")
def root():
    return RedirectResponse(url=settings.API_V1_STR + "/frontend/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
