from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine, SessionLocal

from fastapi.staticfiles import StaticFiles
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

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    if not db.query(Intersection).first():
        # Create sample intersection
        intersection = Intersection(name="Main St & 1st Ave", location="Downtown")
        db.add(intersection)
        db.commit()
        db.refresh(intersection)
        
        # Create lights
        directions = ["North", "South", "East", "West"]
        for direction in directions:
            light = TrafficLight(
                intersection_id=intersection.id,
                direction=direction,
                status="RED" if direction in ["East", "West"] else "GREEN"
            )
            db.add(light)
        db.commit()
    db.close()

@app.get("/")
def root():
    return RedirectResponse(url=settings.API_V1_STR + "/frontend/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
