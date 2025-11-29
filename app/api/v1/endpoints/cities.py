from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.city import City
from app.schemas.city import CityCreate, CityResponse, CityUpdate

router = APIRouter()

@router.post("/", response_model=CityResponse)
def create_city(city: CityCreate, db: Session = Depends(get_db)):
    db_city = City(**city.model_dump())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

from sqlalchemy.orm import joinedload
from app.models.city import TrafficArea
from app.models.intersection import Intersection

@router.get("/", response_model=List[CityResponse])
def read_cities(db: Session = Depends(get_db)):
    cities = db.query(City).all()
    return cities

@router.get("/{city_id}", response_model=CityResponse)
def read_city(city_id: int, db: Session = Depends(get_db)):
    city = db.query(City).options(joinedload(City.areas)).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city

@router.put("/{city_id}", response_model=CityResponse)
def update_city(city_id: int, city_update: CityUpdate, db: Session = Depends(get_db)):
    db_city = db.query(City).filter(City.id == city_id).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")
    
    update_data = city_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_city, key, value)
    
    db.commit()
    db.refresh(db_city)
    return db_city

@router.delete("/{city_id}")
def delete_city(city_id: int, db: Session = Depends(get_db)):
    db_city = db.query(City).filter(City.id == city_id).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")
    
    db.delete(db_city)
    db.commit()
    return {"message": "City deleted"}
