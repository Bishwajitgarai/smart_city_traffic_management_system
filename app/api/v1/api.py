from fastapi import APIRouter
from app.api.v1.endpoints import traffic, frontend, admin, websocket, cities, areas, intersections

api_router = APIRouter()
api_router.include_router(traffic.router, prefix="/traffic-lights", tags=["traffic-lights"])
api_router.include_router(frontend.router, prefix="/frontend", tags=["frontend"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(cities.router, prefix="/cities", tags=["cities"])
api_router.include_router(areas.router, prefix="/areas", tags=["areas"])
api_router.include_router(intersections.router, prefix="/intersections", tags=["intersections"])
api_router.include_router(websocket.router, tags=["websocket"])
