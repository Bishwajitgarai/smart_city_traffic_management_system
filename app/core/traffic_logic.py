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
        # Fetch all lights for this intersection to ensure atomic consistency
        # We need to know which intersection this light belongs to first
        target_light = self.db.query(TrafficLight).filter(TrafficLight.id == light_id).first()
        if not target_light:
            return
            
        intersection_id = target_light.intersection_id
        all_lights = self.db.query(TrafficLight).filter(TrafficLight.intersection_id == intersection_id).all()
        
        # Map lights by direction for easy access
        lights_by_dir = {l.direction: l for l in all_lights}
        target_light = lights_by_dir.get(target_light.direction) # Refresh reference
        
        # Define conflicts
        conflicts = {
            "North": ["East", "West"],
            "South": ["East", "West"],
            "East": ["North", "South"],
            "West": ["North", "South"]
        }
        
        print(f"DEBUG: Setting manual state for {target_light.direction} to {status}")
        
        # 1. Update Target Light
        target_light.is_manual = True
        target_light.status = status
        target_light.last_updated = datetime.now(timezone.utc)
        if duration:
            target_light.duration = duration
            
        # 2. Update Partner Light
        partner_dir = None
        if target_light.direction == "North": partner_dir = "South"
        elif target_light.direction == "South": partner_dir = "North"
        elif target_light.direction == "East": partner_dir = "West"
        elif target_light.direction == "West": partner_dir = "East"
        
        partner_light = lights_by_dir.get(partner_dir)
        if partner_light:
            print(f"DEBUG: Updating partner {partner_dir}")
            partner_light.is_manual = True
            partner_light.status = status
            partner_light.last_updated = datetime.now(timezone.utc)
            if duration:
                partner_light.duration = duration

        # 3. Handle Conflicts (Force RED if Green/Yellow)
        if status in ["GREEN", "YELLOW"]:
            print(f"DEBUG: Checking conflicts for {target_light.direction}")
            for conflict_dir in conflicts.get(target_light.direction, []):
                conflict_light = lights_by_dir.get(conflict_dir)
                if conflict_light:
                    print(f"DEBUG: Forcing conflict {conflict_dir} to RED")
                    # Force conflict to RED
                    conflict_light.status = "RED"
                    conflict_light.is_manual = True
                    conflict_light.last_updated = datetime.now(timezone.utc)
                    conflict_light.duration = target_light.duration # Sync duration
        
        # If setting to RED, we might want to set conflicts to GREEN (Smart Switching)
        # But only if they aren't already manually set to RED? 
        # For safety, let's just ensure we don't leave everyone RED forever if possible,
        # but the user asked for "Smart Switching" (Red -> Green).
        elif status == "RED":
            # Check if we should turn the cross-traffic GREEN
            # This is complex because we don't want to override if the user specifically wanted ALL RED.
            # But based on previous requirements: "Green -> Red: Automatically turns conflicting lights GREEN."
            
            for conflict_dir in conflicts.get(target_light.direction, []):
                conflict_light = lights_by_dir.get(conflict_dir)
                if conflict_light:
                    conflict_light.status = "GREEN"
                    conflict_light.is_manual = True
                    conflict_light.last_updated = datetime.now(timezone.utc)
                    conflict_light.duration = target_light.duration

        self.db.commit()
        
        # 4. Broadcast Updates
        redis = await get_redis()
        from app.api.v1.endpoints.websocket import broadcast_batch_update
        
        end_time = (datetime.now(timezone.utc) + timedelta(seconds=target_light.duration)).timestamp()
        updates = []
        
        # We iterate over all lights to ensure we capture every state change
        for light in all_lights:
            # Update Redis
            await redis.set(f"traffic_light:{light.id}:status", light.status)
            await redis.set(f"traffic_light:{light.id}:end_time", end_time)
            
            updates.append({
                "light_id": light.id,
                "state": {
                    "status": light.status,
                    "end_time": end_time
                }
            })
            
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
        Background task to cycle traffic lights using Optimized 4-Phase Logic:
        0: N/S GREEN  (Duration: light.duration)
        1: N/S YELLOW (Duration: 4s)
        3: E/W GREEN  (Duration: light.duration)
        4: E/W YELLOW (Duration: 4s)
        (Phases 2 and 5 skipped for immediate transition)
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
                        # Phase Expired -> Transition to Next Phase
                        if current_phase == 1:
                            next_phase = 3
                        elif current_phase == 4:
                            next_phase = 0
                        else:
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
                            
                        elif next_phase == 3: # E/W GREEN
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "GREEN")
                            l = ew_lights[0]
                            next_duration = l.duration if l else 60
                            
                        elif next_phase == 4: # E/W YELLOW
                            set_lights(ns_lights, "RED")
                            set_lights(ew_lights, "YELLOW")
                            next_duration = 4
                        
                        # Commit DB
                        db.commit()
                        
                        # Update Redis Phase
                        new_end_time = (datetime.now(timezone.utc) + timedelta(seconds=next_duration)).timestamp()
                        await redis.set(phase_key, next_phase)
                        await redis.set(phase_end_key, new_end_time)
                        
                        # Broadcast Updates
                        batch_updates = []
                        
                        # Helper to get duration
                        def get_duration(dir_code):
                            # dir_code: 'ns' or 'ew'
                            if dir_code == 'ns':
                                l = ns_lights[0]
                                return l.duration if l else 60
                            else:
                                l = ew_lights[0]
                                return l.duration if l else 60

                        ns_dur = get_duration('ns')
                        ew_dur = get_duration('ew')
                        
                        for light_id, status in updates:
                            # Determine direction of this light
                            light_dir = None
                            for l in lights:
                                if l.id == light_id:
                                    light_dir = l.direction
                                    break
                            
                            # Calculate specific end_time
                            # Default to current phase end
                            calculated_end_time = new_end_time
                            
                            if status == "RED":
                                # Calculate time until GREEN
                                remaining_seconds = 0
                                
                                if light_dir in ["North", "South"]:
                                    # Waiting for N/S Green (Phase 0)
                                    if next_phase == 3: # E/W Green
                                        remaining_seconds = ew_dur + 4
                                    elif next_phase == 4: # E/W Yellow
                                        remaining_seconds = 4
                                        
                                elif light_dir in ["East", "West"]:
                                    # Waiting for E/W Green (Phase 3)
                                    if next_phase == 0: # N/S Green
                                        remaining_seconds = ns_dur + 4
                                    elif next_phase == 1: # N/S Yellow
                                        remaining_seconds = 4
                                
                                if remaining_seconds > 0:
                                    calculated_end_time = (datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)).timestamp()

                            # Update individual light keys for UI compatibility
                            # Note: We store the calculated end time in Redis so new clients get the correct countdown
                            await redis.set(f"traffic_light:{light_id}:status", status)
                            await redis.set(f"traffic_light:{light_id}:end_time", calculated_end_time)
                            
                            batch_updates.append({
                                "light_id": light_id,
                                "state": {
                                    "status": status,
                                    "end_time": calculated_end_time
                                }
                            })
                            
                        if batch_updates:
                            try:
                                from app.api.v1.endpoints.websocket import broadcast_batch_update
                                await broadcast_batch_update(batch_updates)
                            except Exception as e:
                                print(f"Broadcast error: {e}")

            except Exception as e:
                print(f"Error in traffic cycle: {e}")
                await asyncio.sleep(5)

    async def _set_light_state(self, light, status, duration, redis):
        # Deprecated, logic moved to run_cycle
        pass
