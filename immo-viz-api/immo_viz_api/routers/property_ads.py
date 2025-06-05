from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import PropertyAd, EnergyConsumptionScore, GESScore
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
    data = payload.dict()

    e_letter = data.pop("energy_consumption", None); g_letter = data.pop("ges", None)
    data["energy_consumption"] = e_letter; data["energy_consumption_score"] = getattr(EnergyConsumptionScore, e_letter).value + 1 if e_letter else None
    data["ges"] = g_letter; data["ges_score"] = getattr(GESScore, g_letter).value + 1 if g_letter else None

    price = data.get("price")
    area = data.get("area")
    data["price_per_m2"] = round(price / area, 2) if price is not None and area != 0 else None

    new_property_ad = PropertyAd(**data)
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
    """Update a property_ad by id."""
    logger.info("Updating property_ad with id: %d", property_ad_id)
    property_ad = db.query(PropertyAd).filter(PropertyAd.id == property_ad_id).first()
    if not property_ad:
        logger.warning("PropertyAd with id %d not found", property_ad_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PropertyAd not found"
        )

    data = payload.dict()
    e_letter = data.pop("energy_consumption", None)
    g_letter = data.pop("ges", None)

    if e_letter is not None:
        setattr(property_ad, "energy_consumption", e_letter)
        setattr(
            property_ad,
            "energy_consumption_score",
            getattr(EnergyConsumptionScore, e_letter).value + 1,
        )
    else:
        setattr(property_ad, "energy_consumption", None)
        setattr(property_ad, "energy_consumption_score", None)

    if g_letter is not None:
        setattr(property_ad, "ges", g_letter)
        setattr(property_ad, "ges_score", getattr(GESScore, g_letter).value + 1)
    else:
        setattr(property_ad, "ges", None)
        setattr(property_ad, "ges_score", None)

    for key, value in data.items():
        setattr(property_ad, key, value)

    db.commit()
    db.refresh(property_ad)
    logger.info("PropertyAd with id %d updated successfully", property_ad.id)
    return property_ad


@router.delete("/{property_ad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_ad(property_ad_id: int, db: Session = Depends(get_viz_db)):
    """Delete a property_ad by id."""
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
