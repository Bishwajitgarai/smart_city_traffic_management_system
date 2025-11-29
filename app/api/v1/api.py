from fastapi import APIRouter
from app.api.v1.endpoints import traffic, frontend

api_router = APIRouter()
api_router.include_router(traffic.router, prefix="/traffic-lights", tags=["traffic-lights"])
api_router.include_router(frontend.router, prefix="/frontend", tags=["frontend"])
