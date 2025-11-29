from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)
    
    areas = relationship("TrafficArea", back_populates="city")

class TrafficArea(Base):
    __tablename__ = "traffic_areas"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    name = Column(String, index=True)
    code = Column(String, index=True)
    
    city = relationship("City", back_populates="areas")
    intersections = relationship("Intersection", back_populates="area")
