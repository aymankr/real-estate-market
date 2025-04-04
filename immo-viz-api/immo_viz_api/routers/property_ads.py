from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import PropertyAd
from immo_viz_api.schemas import PropertyAdCreate, PropertyAdResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/property_ads", tags=["PropertyAd"])


@router.post(
    "/", response_model=PropertyAdResponse, status_code=status.HTTP_201_CREATED
)
def create_property_ad(payload: PropertyAdCreate, db: Session = Depends(get_viz_db)):
    """Create a new property_ad."""
    logger.info("Creating a new property_ad")
    new_property_ad = PropertyAd(**payload.dict())
    new_property_ad.inserted_at = datetime.now()
    db.add(new_property_ad)
    db.commit()
    db.refresh(new_property_ad)
    logger.info("PropertyAd created with id: %d", new_property_ad.id)
    return new_property_ad


@router.get("/", response_model=List[PropertyAdResponse])
def get_property_ads(db: Session = Depends(get_viz_db), limit: int = 10, skip: int = 0):
    """Retrieve a list of property_ads with pagination."""
    logger.info("Fetching property_ads with limit=%d and skip=%d", limit, skip)
    property_ads = db.query(PropertyAd).offset(skip).limit(limit).all()
    return property_ads


@router.get("/{property_ad_id}", response_model=PropertyAdResponse)
def get_property_ad(property_ad_id: int, db: Session = Depends(get_viz_db)):
    """Get a specific property_ad by id."""
    logger.info("Fetching property_ad with id: %d", property_ad_id)
    property_ad = db.query(PropertyAd).filter(PropertyAd.id == property_ad_id).first()
    if not property_ad:
        logger.warning("PropertyAd with id %d not found", property_ad_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PropertyAd not found"
        )
    return property_ad


@router.put("/{property_ad_id}", response_model=PropertyAdResponse)
def update_property_ad(
    property_ad_id: int, payload: PropertyAdCreate, db: Session = Depends(get_viz_db)
):
    """Update an property_ad by id."""
    logger.info("Updating property_ad with id: %d", property_ad_id)
    property_ad = db.query(PropertyAd).filter(PropertyAd.id == property_ad_id).first()
    if not property_ad:
        logger.warning("PropertyAd with id %d not found", property_ad_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PropertyAd not found"
        )

    for key, value in payload.dict().items():
        setattr(property_ad, key, value)

    db.commit()
    db.refresh(property_ad)
    logger.info("PropertyAd with id %d updated successfully", property_ad.id)
    return property_ad


@router.delete("/{property_ad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_ad(property_ad_id: int, db: Session = Depends(get_viz_db)):
    """Delete an property_ad by id."""
    logger.info("Deleting property_ad with id: %d", property_ad_id)
    property_ad = db.query(PropertyAd).filter(PropertyAd.id == property_ad_id).first()
    if not property_ad:
        logger.warning("PropertyAd with id %d not found", property_ad_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PropertyAd not found"
        )

    db.delete(property_ad)
    db.commit()
    logger.info("PropertyAd with id %d deleted successfully", property_ad_id)
    return {"detail": "PropertyAd deleted successfully"}
