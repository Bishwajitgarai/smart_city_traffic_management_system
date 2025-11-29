from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Intersection(Base):
    __tablename__ = "intersections"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("traffic_areas.id"))
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    location = Column(String)
    
    area = relationship("TrafficArea", back_populates="intersections")
    traffic_lights = relationship("TrafficLight", back_populates="intersection")
