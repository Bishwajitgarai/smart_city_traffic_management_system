from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class TrafficLight(Base):
    __tablename__ = "traffic_lights"

    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(Integer, ForeignKey("intersections.id"))
    direction = Column(String)  # North, South, East, West
    status = Column(String, default="RED")  # RED, YELLOW, GREEN
    current_density = Column(Integer, default=0)
    duration = Column(Integer, default=60) # Duration in seconds
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    is_manual = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    intersection = relationship("Intersection", back_populates="traffic_lights")
