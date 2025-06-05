from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import Department
from immo_viz_api.schemas import DepartmentCreate, DepartmentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments", tags=["Department"])


@router.post(
    "/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED
)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_viz_db)):
    """Create a new department."""
    logger.info("Creating a new department with insee_code: %s", payload.department_insee_code)
    new_department = Department(**payload.dict())
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    logger.info("Department created with insee_code: %d", new_department.department_insee_code)
    return new_department


@router.get("/", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_viz_db), limit: int = 10, skip: int = 0):
    """Retrieve a list of departments with pagination."""
    logger.info("Fetching departments with limit=%d and skip=%d", limit, skip)
    departments = db.query(Department).offset(skip).limit(limit).all()
    return departments


@router.get("/{department_insee_code}", response_model=DepartmentResponse)
def get_department(department_insee_code: int, db: Session = Depends(get_viz_db)):
    """Get a specific department by insee_code."""
    logger.info("Fetching department with insee_code: %d", department_insee_code)
    department = db.query(Department).filter(Department.department_insee_code == department_insee_code).first()
    if not department:
        logger.warning("Department with insee_code %d not found", department_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    return department


@router.put("/{department_insee_code}", response_model=DepartmentResponse)
def update_department(
    department_insee_code: int, payload: DepartmentCreate, db: Session = Depends(get_viz_db)
):
    """Update an department by insee_code."""
    logger.info("Updating department with insee_code: %d", department_insee_code)
    department = db.query(Department).filter(Department.department_insee_code == department_insee_code).first()
    if not department:
        logger.warning("Department with insee_code %d not found", department_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    for key, value in payload.dict().items():
        setattr(department, key, value)

    db.commit()
    db.refresh(department)
    logger.info("Department with insee_code %d updated successfully", department.department_insee_code)
    return department


@router.delete("/{department_insee_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_insee_code: int, db: Session = Depends(get_viz_db)):
    """Delete an department by insee_code."""
    logger.info("Deleting department with insee_code: %d", department_insee_code)
    department = db.query(Department).filter(Department.department_insee_code == department_insee_code).first()
    if not department:
        logger.warning("Department with insee_code %d not found", department_insee_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    db.delete(department)
    db.commit()
    logger.info("Department with insee_code %d deleted successfully", department_insee_code)
    return {"detail": "Department deleted successfully"}
