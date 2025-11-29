import sys
import os

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.city import City, TrafficArea
from app.models.intersection import Intersection
from app.models.traffic import TrafficLight

def seed_data():
    db = SessionLocal()
    try:
        if not db.query(City).first():
            print("Seeding data...")
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
            print("Seeding complete.")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

def reset_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    seed_data()
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_db()
