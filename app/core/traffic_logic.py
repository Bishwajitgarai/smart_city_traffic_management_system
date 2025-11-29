import asyncio
from sqlalchemy.orm import Session
from app.models.traffic import TrafficLight
from app.models.intersection import Intersection
from app.services.redis import get_redis

class TrafficController:
    def __init__(self, db: Session):
        self.db = db

    async def cycle_intersection(self, intersection_id: int):
        """
        Simple logic to cycle lights in an intersection.
        In a real scenario, this would be more complex and run in a background task.
        """
        lights = self.db.query(TrafficLight).filter(TrafficLight.intersection_id == intersection_id).all()
        
        # Simple round-robin or based on density
        # For now, let's just find the one with highest density and make it GREEN, others RED
        
        if not lights:
            return

        # Sort by density desc
        lights.sort(key=lambda x: x.current_density, reverse=True)
        
        highest_density_light = lights[0]
        
        redis = await get_redis()

        for light in lights:
            new_status = "RED"
            if light.id == highest_density_light.id:
                new_status = "GREEN"
            
            if light.status != new_status:
                light.status = new_status
                # Update Redis
                await redis.set(f"traffic_light:{light.id}:status", new_status)
        
        self.db.commit()

    async def update_density(self, traffic_light_id: int, new_density: int):
        light = self.db.query(TrafficLight).filter(TrafficLight.id == traffic_light_id).first()
        if light:
            light.current_density = new_density
            self.db.commit()
            # Trigger cycle check
            await self.cycle_intersection(light.intersection_id)
