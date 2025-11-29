import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.traffic import TrafficLight
from app.models.intersection import Intersection
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
            
        intersection_id = light.intersection_id
        
        # Partner Logic: Identify partner (N<->S, E<->W)
        partner_direction = None
        if light.direction == "North": partner_direction = "South"
        elif light.direction == "South": partner_direction = "North"
        elif light.direction == "East": partner_direction = "West"
        elif light.direction == "West": partner_direction = "East"
        
        # Conflicting Logic: Identify cross traffic
        conflicting_directions = []
        if light.direction in ["North", "South"]:
            conflicting_directions = ["East", "West"]
        elif light.direction in ["East", "West"]:
            conflicting_directions = ["North", "South"]

        # 1. Update Primary Light
        light.is_manual = True
        light.status = status
        light.last_updated = datetime.now(timezone.utc)
        if duration:
            light.duration = duration
            
        # 2. Update Partner Light (Sync Status)
        partner_light = self.db.query(TrafficLight).filter(
            TrafficLight.intersection_id == intersection_id,
            TrafficLight.direction == partner_direction
        ).first()
        
        if partner_light:
            partner_light.is_manual = True
            partner_light.status = status
            partner_light.last_updated = datetime.now(timezone.utc)
            if duration:
                partner_light.duration = duration

        # 3. Update Conflicting Lights (Force RED if Primary is GREEN)
        conflicting_lights = self.db.query(TrafficLight).filter(
            TrafficLight.intersection_id == intersection_id,
            TrafficLight.direction.in_(conflicting_directions)
        ).all()
        
        redis = await get_redis()
        from app.api.v1.endpoints.websocket import broadcast_state_update, broadcast_batch_update
        
        # Calculate End Time (shared for all affected lights)
        end_time = (datetime.now(timezone.utc) + timedelta(seconds=light.duration)).timestamp()
        
        updates = []
        
        if status == "GREEN":
            for conflict in conflicting_lights:
                if conflict.status != "RED":
                    conflict.status = "RED"
                    conflict.is_manual = True
                    conflict.last_updated = datetime.now(timezone.utc)
                    conflict.duration = light.duration # Sync duration
                    
                    # Update Redis for conflict
                    await redis.set(f"traffic_light:{conflict.id}:status", "RED")
                    await redis.set(f"traffic_light:{conflict.id}:end_time", end_time)
                    
                    # Add to batch
                    updates.append({
                        "light_id": conflict.id,
                        "state": {
                            "status": "RED",
                            "end_time": end_time
                        }
                    })
        elif status == "RED":
            for conflict in conflicting_lights:
                if conflict.status != "GREEN":
                    conflict.status = "GREEN"
                    conflict.is_manual = True
                    conflict.last_updated = datetime.now(timezone.utc)
                    conflict.duration = light.duration # Sync duration
                    
                    # Update Redis for conflict
                    await redis.set(f"traffic_light:{conflict.id}:status", "GREEN")
                    await redis.set(f"traffic_light:{conflict.id}:end_time", end_time)
                    
                    # Add to batch
                    updates.append({
                        "light_id": conflict.id,
                        "state": {
                            "status": "GREEN",
                            "end_time": end_time
                        }
                    })
        
        self.db.commit()
        
        # Update Redis & Broadcast for Primary & Partner
        
        # Primary
        await redis.set(f"traffic_light:{light.id}:status", status)
        await redis.set(f"traffic_light:{light.id}:end_time", end_time)
        updates.append({
            "light_id": light.id,
            "state": {"status": status, "end_time": end_time}
        })
        
        if partner_light:
            await redis.set(f"traffic_light:{partner_light.id}:status", status)
            await redis.set(f"traffic_light:{partner_light.id}:end_time", end_time)
            updates.append({
                "light_id": partner_light.id,
                "state": {"status": status, "end_time": end_time}
            })
            
        # Send all updates in one batch
        if updates:
            await broadcast_batch_update(updates)

    async def reset_manual_state(self, light_id: int):
        light = self.db.query(TrafficLight).filter(TrafficLight.id == light_id).first()
        if not light:
            return
            
        light.is_manual = False
        light.last_updated = datetime.now(timezone.utc)
        self.db.commit()
        
        # Remove from Redis manual override
        # We don't delete the status key, just let the cycle overwrite it eventually
        pass

    async def update_density(self, traffic_light_id: int, new_density: int):
        light = self.db.query(TrafficLight).filter(TrafficLight.id == traffic_light_id).first()
        if light:
            light.current_density = new_density
            self.db.commit()

    async def run_cycle(self):
        """
        Background task to cycle traffic lights using Real-World 6-Phase Logic:
        0: N/S GREEN  (Duration: light.duration)
        1: N/S YELLOW (Duration: 4s)
        2: ALL RED    (Duration: 2s) - Safety Clearance
        3: E/W GREEN  (Duration: light.duration)
        4: E/W YELLOW (Duration: 4s)
        5: ALL RED    (Duration: 2s) - Safety Clearance
        """
        from app.api.v1.endpoints.websocket import broadcast_state_update
        from app.db.session import SessionLocal
        
        print("🚦 Real-World Traffic Controller Started")
        
        while True:
            await asyncio.sleep(1)
            
            try:
                with SessionLocal() as db:
                    redis = await get_redis()
                    
                    # Check for expired manual lights
                    manual_lights = db.query(TrafficLight).filter(TrafficLight.is_manual == True).all()
                    for light in manual_lights:
                        # Calculate expiration
                        last_updated = light.last_updated
                        if last_updated.tzinfo is None:
                            last_updated = last_updated.replace(tzinfo=timezone.utc)
                            
                        expiration = last_updated + timedelta(seconds=light.duration)
                        
                        if datetime.now(timezone.utc) > expiration:
                            # Revert to Auto
                            light.is_manual = False
                            
                            # Sync to current intersection phase immediately
                            phase_key = f"intersection:{light.intersection_id}:phase"
                            phase_end_key = f"intersection:{light.intersection_id}:phase_end"
                            
                            phase_str = await redis.get(phase_key)
                            phase_end_str = await redis.get(phase_end_key)
                            
                            if phase_str and phase_end_str:
                                current_phase = int(phase_str)
                                phase_end = float(phase_end_str)
                                
                                # Determine correct status based on phase
                                new_status = "RED"
                                if light.direction in ["North", "South"]:
                                    if current_phase == 0: new_status = "GREEN"
                                    elif current_phase == 1: new_status = "YELLOW"
                                elif light.direction in ["East", "West"]:
                                    if current_phase == 3: new_status = "GREEN"
                                    elif current_phase == 4: new_status = "YELLOW"
                                
                                light.status = new_status
                                light.last_updated = datetime.now(timezone.utc)
                                
                                # Update Redis & Broadcast
                                await redis.set(f"traffic_light:{light.id}:status", new_status)
                                await redis.set(f"traffic_light:{light.id}:end_time", phase_end)
                                await broadcast_state_update(light.id, {
                                    "status": new_status,
                                    "end_time": phase_end
                                })
                            
                            db.commit()
                    
                    intersections = db.query(Intersection).all()
                    
                    for intersection in intersections:
                        # Get current phase from Redis (default to 0)
                        phase_key = f"intersection:{intersection.id}:phase"
                        phase_str = await redis.get(phase_key)
                        current_phase = int(phase_str) if phase_str else 0
                        
                        # Get end time of current phase
                        phase_end_key = f"intersection:{intersection.id}:phase_end"
                        phase_end_str = await redis.get(phase_end_key)
                        
                        # Initialize if missing
                        if not phase_end_str:
                            # Default to Phase 0 (N/S Green)
                            current_phase = 0
                            # Find N/S duration
                            ns_light = db.query(TrafficLight).filter(
                                TrafficLight.intersection_id == intersection.id,
                                TrafficLight.direction == "North"
                            ).first()
                            duration = ns_light.duration if ns_light else 60
                            
                            new_end = (datetime.now(timezone.utc) + timedelta(seconds=duration)).timestamp()
                            await redis.set(phase_key, 0)
                            await redis.set(phase_end_key, new_end)
                            continue
                            
                        # Check if phase expired
                        if datetime.now(timezone.utc).timestamp() < float(phase_end_str):
                            continue
                            
                        # Phase Expired -> Transition to Next Phase
                        next_phase = (current_phase + 1) % 6
                        # print(f"Intersection {intersection.id}: Phase {current_phase} -> {next_phase}")
                        
                        lights = db.query(TrafficLight).filter(
                            TrafficLight.intersection_id == intersection.id,
                            TrafficLight.is_manual == False
                        ).all()
                        lights_dict = {l.direction: l for l in lights}
                        ns_lights = [lights_dict.get("North"), lights_dict.get("South")]
                        ew_lights = [lights_dict.get("East"), lights_dict.get("West")]
                        
                        updates = []
                        next_duration = 2 # Default safety
                        
                        def set_lights(light_list, status):
                            for l in light_list:
                                if l:
                                    l.status = status
                                    l.last_updated = datetime.now(timezone.utc)
                                    updates.append((l.id, status))

                        # Logic for Next Phase
                        if next_phase == 0: # N/S GREEN
                            set_lights(ns_lights, "GREEN")
                            set_lights(ew_lights, "RED")
                            # Get duration from DB
                            l = ns_lights[0]
                            next_duration = l.duration if l else 60
                            
                        elif next_phase == 1: # N/S YELLOW
                            set_lights(ns_lights, "YELLOW")
                            set_lights(ew_lights, "RED")
                            next_duration = 4
                            
                        elif next_phase == 2: # ALL RED (Clearance)
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "RED")
                            next_duration = 2
                            
                        elif next_phase == 3: # E/W GREEN
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "GREEN")
                            l = ew_lights[0]
                            next_duration = l.duration if l else 60
                            
                        elif next_phase == 4: # E/W YELLOW
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "YELLOW")
                            next_duration = 4
                            
                        elif next_phase == 5: # ALL RED (Clearance)
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "RED")
                            next_duration = 2
                        
                        # Commit DB
                        db.commit()
                        
                        # Update Redis Phase
                        new_end_time = (datetime.now(timezone.utc) + timedelta(seconds=next_duration)).timestamp()
                        await redis.set(phase_key, next_phase)
                        await redis.set(phase_end_key, new_end_time)
                        
                        # Broadcast Updates
                        for light_id, status in updates:
                            # Update individual light keys for UI compatibility
                            await redis.set(f"traffic_light:{light_id}:status", status)
                            await redis.set(f"traffic_light:{light_id}:end_time", new_end_time)
                            
                            try:
                                await broadcast_state_update(light_id, {
                                    "status": status,
                                    "end_time": new_end_time
                                })
                            except Exception as e:
                                print(f"Broadcast error: {e}")

            except Exception as e:
                print(f"Error in traffic cycle: {e}")
                await asyncio.sleep(5)

    async def _set_light_state(self, light, status, duration, redis):
        # Deprecated, logic moved to run_cycle
        pass
