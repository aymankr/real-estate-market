from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import Region
from immo_viz_api.schemas import RegionCreate, RegionResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["Regions"])


@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
def create_region(payload: RegionCreate, db: Session = Depends(get_viz_db)):
    """Create a new region."""
    logger.info("Creating a new region with message: %s", payload.message)
    new_region = Region(**payload.dict())
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    logger.info("Region created with insee_code: %d", new_region.insee_code)
    return new_region


@router.get("/", response_model=List[RegionResponse])
def get_regions(db: Session = Depends(get_viz_db), limit: int = 10, skip: int = 0):
    """Retrieve a list of regions with pagination."""
    logger.info("Fetching regions with limit=%d and skip=%d", limit, skip)
    regions = db.query(Region).offset(skip).limit(limit).all()
    return regions


@router.get("/{region_code}", response_model=RegionResponse)
def get_region(region_code: int, db: Session = Depends(get_viz_db)):
    """Get a specific region by insee_code."""
    logger.info("Fetching region with insee_code: %d", region_code)
    region = db.query(Region).filter(Region.insee_code == region_code).first()
    if not region:
        logger.warning("Region with insee_code %d not found", region_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
        )
    return region


@router.put("/{region_code}", response_model=RegionResponse)
def update_region(
    region_code: int, payload: RegionCreate, db: Session = Depends(get_viz_db)
):
    """Update an region by insee_code."""
    logger.info("Updating region with insee_code: %d", region_code)
    region = db.query(Region).filter(Region.insee_code == region_code).first()
    if not region:
        logger.warning("Region with insee_code %d not found", region_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
        )

    for key, value in payload.dict().items():
        setattr(region, key, value)

    db.commit()
    db.refresh(region)
    logger.info("Region with insee_code %d updated successfully", region.insee_code)
    return region


@router.delete("/{region_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(region_code: int, db: Session = Depends(get_viz_db)):
    """Delete an region by insee_code."""
    logger.info("Deleting region with insee_code: %d", region_code)
    region = db.query(Region).filter(Region.insee_code == region_code).first()
    if not region:
        logger.warning("Region with insee_code %d not found", region_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
        )

    db.delete(region)
    db.commit()
    logger.info("Region with insee_code %d deleted successfully", region_code)
    return {"detail": "Region deleted successfully"}
