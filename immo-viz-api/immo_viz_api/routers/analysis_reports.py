from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_monitoring_db
from immo_viz_api.models import AnalysisReport
from immo_viz_api.schemas import AnalysisReportCreate, AnalysisReportResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis_reports", tags=["AnalysisReport"])


@router.post(
    "/", response_model=AnalysisReportResponse, status_code=status.HTTP_201_CREATED
)
def create_analysis_report(
    payload: AnalysisReportCreate, db: Session = Depends(get_monitoring_db)
):
    """Create a new analysis_report."""
    logger.info("Creating a new analysis_report")
    new_analysis_report = AnalysisReport(**payload.dict())
    new_analysis_report.inserted_at = datetime.now()
    db.add(new_analysis_report)
    db.commit()
    db.refresh(new_analysis_report)
    logger.info("AnalysisReport created with id: %d", new_analysis_report.id)
    return new_analysis_report


@router.get("/", response_model=List[AnalysisReportResponse])
def get_analysis_reports(
    db: Session = Depends(get_monitoring_db), limit: int = 10, skip: int = 0
):
    """Retrieve a list of analysis_reports with pagination."""
    logger.info("Analysis analysis_reports with limit=%d and skip=%d", limit, skip)
    analysis_reports = db.query(AnalysisReport).offset(skip).limit(limit).all()
    return analysis_reports


@router.get("/{analysis_report_id}", response_model=AnalysisReportResponse)
def get_analysis_report(analysis_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Get a specific analysis_report by id."""
    logger.info("Analysis analysis_report with id: %d", analysis_report_id)
    analysis_report = (
        db.query(AnalysisReport).filter(AnalysisReport.id == analysis_report_id).first()
    )
    if not analysis_report:
        logger.warning("AnalysisReport with id %d not found", analysis_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AnalysisReport not found"
        )
    return analysis_report


@router.put("/{analysis_report_id}", response_model=AnalysisReportResponse)
def update_analysis_report(
    analysis_report_id: int,
    payload: AnalysisReportCreate,
    db: Session = Depends(get_monitoring_db),
):
    """Update an analysis_report by id."""
    logger.info("Updating analysis_report with id: %d", analysis_report_id)
    analysis_report = (
        db.query(AnalysisReport).filter(AnalysisReport.id == analysis_report_id).first()
    )
    if not analysis_report:
        logger.warning("AnalysisReport with id %d not found", analysis_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AnalysisReport not found"
        )

    for key, value in payload.dict().items():
        setattr(analysis_report, key, value)

    db.commit()
    db.refresh(analysis_report)
    logger.info("AnalysisReport with id %d updated successfully", analysis_report.id)
    return analysis_report


@router.delete("/{analysis_report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis_report(analysis_report_id: int, db: Session = Depends(get_monitoring_db)):
    """Delete an analysis_report by id."""
    logger.info("Deleting analysis_report with id: %d", analysis_report_id)
    analysis_report = (
        db.query(AnalysisReport).filter(AnalysisReport.id == analysis_report_id).first()
    )
    if not analysis_report:
        logger.warning("AnalysisReport with id %d not found", analysis_report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AnalysisReport not found"
        )

    db.delete(analysis_report)
    db.commit()
    logger.info("AnalysisReport with id %d deleted successfully", analysis_report_id)
    return {"detail": "AnalysisReport deleted successfully"}
