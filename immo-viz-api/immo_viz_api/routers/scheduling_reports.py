from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_monitoring_db
from immo_viz_api.models import SchedulingReport
from immo_viz_api.schemas import SchedulingReportCreate, SchedulingReportResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduling_reports", tags=["SchedulingReport"])


@router.post(
    "/", response_model=SchedulingReportResponse, status_code=status.HTTP_201_CREATED
)
def create_scheduling_report(
    payload: SchedulingReportCreate, db: Session = Depends(get_monitoring_db)
):
    """Create a new scheduling_report."""
    logger.info("Creating a new scheduling_report")
    new_scheduling_report = SchedulingReport(**payload.dict())
    new_scheduling_report.inserted_at = datetime.now()
    db.add(new_scheduling_report)
    db.commit()
    db.refresh(new_scheduling_report)
    logger.info("SchedulingReport created with id: %d", new_scheduling_report.id)
    return new_scheduling_report


@router.get("/", response_model=List[SchedulingReportResponse])
def get_scheduling_reports(
    db: Session = Depends(get_monitoring_db), limit: int = 10, skip: int = 0
):
    """Retrieve a list of scheduling_reports with pagination."""
    logger.info("Scheduling scheduling_reports with limit=%d and skip=%d", limit, skip)
    scheduling_reports = db.query(SchedulingReport).offset(skip).limit(limit).all()
    return scheduling_reports


@router.get("/{scheduling_report_id}", response_model=SchedulingReportResponse)
def get_scheduling_report(scheduling_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Get a specific scheduling_report by id."""
    logger.info("Scheduling scheduling_report with id: %d", scheduling_report_id)
    scheduling_report = (
        db.query(SchedulingReport).filter(SchedulingReport.id == scheduling_report_id).first()
    )
    if not scheduling_report:
        logger.warning("SchedulingReport with id %d not found", scheduling_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SchedulingReport not found"
        )
    return scheduling_report


@router.put("/{scheduling_report_id}", response_model=SchedulingReportResponse)
def update_scheduling_report(
    scheduling_report_id: int,
    payload: SchedulingReportCreate,
    db: Session = Depends(get_monitoring_db),
):
    """Update an scheduling_report by id."""
    logger.info("Updating scheduling_report with id: %d", scheduling_report_id)
    scheduling_report = (
        db.query(SchedulingReport).filter(SchedulingReport.id == scheduling_report_id).first()
    )
    if not scheduling_report:
        logger.warning("SchedulingReport with id %d not found", scheduling_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SchedulingReport not found"
        )

    for key, value in payload.dict().items():
        setattr(scheduling_report, key, value)

    db.commit()
    db.refresh(scheduling_report)
    logger.info("SchedulingReport with id %d updated successfully", scheduling_report.id)
    return scheduling_report


@router.delete("/{scheduling_report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduling_report(scheduling_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Delete an scheduling_report by id."""
    logger.info("Deleting scheduling_report with id: %d", scheduling_report_id)
    scheduling_report = (
        db.query(SchedulingReport).filter(SchedulingReport.id == scheduling_report_id).first()
    )
    if not scheduling_report:
        logger.warning("SchedulingReport with id %d not found", scheduling_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="SchedulingReport not found"
        )

    db.delete(scheduling_report)
    db.commit()
    logger.info("SchedulingReport with id %d deleted successfully", scheduling_report_id)
    return {"detail": "SchedulingReport deleted successfully"}
