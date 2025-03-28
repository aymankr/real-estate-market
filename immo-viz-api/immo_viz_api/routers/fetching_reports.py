from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_monitoring_db
from immo_viz_api.models import FetchingReport
from immo_viz_api.schemas import FetchingReportCreate, FetchingReportResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetching_reports", tags=["FetchingReport"])


@router.post(
    "/", response_model=FetchingReportResponse, status_code=status.HTTP_201_CREATED
)
def create_fetching_report(
    payload: FetchingReportCreate, db: Session = Depends(get_monitoring_db)
):
    """Create a new fetching_report."""
    logger.info("Creating a new fetching_report")
    new_fetching_report = FetchingReport(**payload.dict())
    new_fetching_report.inserted_at = datetime.now()
    db.add(new_fetching_report)
    db.commit()
    db.refresh(new_fetching_report)
    logger.info("FetchingReport created with id: %d", new_fetching_report.id)
    return new_fetching_report


@router.get("/", response_model=List[FetchingReportResponse])
def get_fetching_reports(
    db: Session = Depends(get_monitoring_db), limit: int = 10, skip: int = 0
):
    """Retrieve a list of fetching_reports with pagination."""
    logger.info("Fetching fetching_reports with limit=%d and skip=%d", limit, skip)
    fetching_reports = db.query(FetchingReport).offset(skip).limit(limit).all()
    return fetching_reports


@router.get("/{fetching_report_id}", response_model=FetchingReportResponse)
def get_fetching_report(fetching_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Get a specific fetching_report by id."""
    logger.info("Fetching fetching_report with id: %d", fetching_report_id)
    fetching_report = (
        db.query(FetchingReport).filter(FetchingReport.id == fetching_report_id).first()
    )
    if not fetching_report:
        logger.warning("FetchingReport with id %d not found", fetching_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="FetchingReport not found"
        )
    return fetching_report


@router.put("/{fetching_report_id}", response_model=FetchingReportResponse)
def update_fetching_report(
    fetching_report_id: int,
    payload: FetchingReportCreate,
    db: Session = Depends(get_monitoring_db),
):
    """Update an fetching_report by id."""
    logger.info("Updating fetching_report with id: %d", fetching_report_id)
    fetching_report = (
        db.query(FetchingReport).filter(FetchingReport.id == fetching_report_id).first()
    )
    if not fetching_report:
        logger.warning("FetchingReport with id %d not found", fetching_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="FetchingReport not found"
        )

    for key, value in payload.dict().items():
        setattr(fetching_report, key, value)

    db.commit()
    db.refresh(fetching_report)
    logger.info("FetchingReport with id %d updated successfully", fetching_report.id)
    return fetching_report


@router.delete("/{fetching_report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fetching_report(fetching_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Delete an fetching_report by id."""
    logger.info("Deleting fetching_report with id: %d", fetching_report_id)
    fetching_report = (
        db.query(FetchingReport).filter(FetchingReport.id == fetching_report_id).first()
    )
    if not fetching_report:
        logger.warning("FetchingReport with id %d not found", fetching_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="FetchingReport not found"
        )

    db.delete(fetching_report)
    db.commit()
    logger.info("FetchingReport with id %d deleted successfully", fetching_report_id)
    return {"detail": "FetchingReport deleted successfully"}
