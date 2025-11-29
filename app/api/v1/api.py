from fastapi import APIRouter
from app.api.v1.endpoints import traffic

api_router = APIRouter()
api_router.include_router(traffic.router, prefix="/traffic-lights", tags=["traffic-lights"])
