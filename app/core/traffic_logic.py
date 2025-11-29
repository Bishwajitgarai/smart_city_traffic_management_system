import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.traffic import TrafficLight
from app.services.redis import get_redis

class TrafficController:
    def __init__(self, db: Session):
        self.db = db

    async def get_state(self, light_id: int):
        redis = await get_redis()
        end_time = await redis.get(f"traffic_light:{light_id}:end_time")
        status = await redis.get(f"traffic_light:{light_id}:status")
        
        # Fallback to DB if Redis is empty
        if not status:
            light = self.db.query(TrafficLight).filter(TrafficLight.id == light_id).first()
            if light:
                status = light.status
                # If no end time, assume it just started or is manual
                if not end_time:
                    end_time = (datetime.now(timezone.utc) + timedelta(seconds=light.duration)).timestamp()
        
        return {
            "status": status,
            "end_time": float(end_time) if end_time else None
        }

    async def set_manual_state(self, light_id: int, status: str, duration: int = None):
        light = self.db.query(TrafficLight).filter(TrafficLight.id == light_id).first()
        if not light:
            return
        
        light.is_manual = True
        light.status = status
        light.last_updated = datetime.now(timezone.utc)
        if duration:
            light.duration = duration
        
        self.db.commit()
        
        redis = await get_redis()
        await redis.set(f"traffic_light:{light_id}:status", status)
        # Manual mode might mean indefinite, but let's set a long expiry or handle it in frontend
        # For now, let's set the end_time based on duration
        end_time = (datetime.now(timezone.utc) + timedelta(seconds=light.duration)).timestamp()
        await redis.set(f"traffic_light:{light_id}:end_time", end_time)

    async def update_density(self, traffic_light_id: int, new_density: int):
        light = self.db.query(TrafficLight).filter(TrafficLight.id == traffic_light_id).first()
        if light:
            light.current_density = new_density
            self.db.commit()
            # In a real system, this would trigger a re-evaluation of the cycle
            # For this demo, we'll just update the density value

    async def run_cycle(self, intersection_id: int):
        # This function would be called periodically by a background worker
        # It checks if the current phase is over and switches to the next
        pass
