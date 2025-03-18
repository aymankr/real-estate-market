from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import City
from immo_viz_api.schemas import CityCreate, CityResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cities", tags=["City"])


@router.post("/", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(payload: CityCreate, db: Session = Depends(get_viz_db)):
    """Create a new city."""
    logger.info("Creating a new city with message: %s", payload.message)
    new_city = City(**payload.dict())
    db.add(new_city)
    db.commit()
    db.refresh(new_city)
    logger.info("City created with insee_code: %d", new_city.insee_code)
    return new_city


@router.get("/", response_model=List[CityResponse])
def get_cities(db: Session = Depends(get_viz_db), limit: int = 10, skip: int = 0):
    """Retrieve a list of cities with pagination."""
    logger.info("Fetching cities with limit=%d and skip=%d", limit, skip)
    cities = db.query(City).offset(skip).limit(limit).all()
    return cities


@router.get("/{city_insee_code}", response_model=CityResponse)
def get_city(city_insee_code: str, db: Session = Depends(get_viz_db)):
    """Get a specific city by city_insee_code."""
    logger.info("Fetching city with city_insee_code: %d", city_insee_code)
    city = db.query(City).filter(City.insee_code == city_insee_code).first()
    if not city:
        logger.warning("City with city_insee_code %d not found", city_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    return city


@router.put("/{city_insee_code}", response_model=CityResponse)
def update_city(city_insee_code: str, payload: CityCreate, db: Session = Depends(get_viz_db)):
    """Update an city by city_insee_code."""
    logger.info("Updating city with city_insee_code: %d", city_insee_code)
    city = db.query(City).filter(City.insee_code == city_insee_code).first()
    if not city:
        logger.warning("City with city_insee_code %d not found", city_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    for key, value in payload.dict().items():
        setattr(city, key, value)

    db.commit()
    db.refresh(city)
    logger.info("City with city_insee_code %d updated successfully", city.insee_code)
    return city


@router.delete("/{city_insee_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_city(city_insee_code: str, db: Session = Depends(get_viz_db)):
    """Delete an city by city_insee_code."""
    logger.info("Deleting city with city_insee_code: %d", city_insee_code)
    city = db.query(City).filter(City.insee_code == city_insee_code).first()
    if not city:
        logger.warning("City with city_insee_code %d not found", city_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )

    db.delete(city)
    db.commit()
    logger.info("City with city_insee_code %d deleted successfully", city_insee_code)
    return {"detail": "City deleted successfully"}
