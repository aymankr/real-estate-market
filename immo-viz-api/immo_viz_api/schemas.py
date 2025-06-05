from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from immo_viz_api.models import BuildingType, EnergyConsumption, GES


# --- Viz database CRUD schemas --- #
class RegionCreate(BaseModel):
    region_insee_code: str
    name: str
    area: Optional[float] = None
    population: Optional[int] = None
    capital_city_insee_code: Optional[str] = None


class RegionResponse(RegionCreate):
    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    department_insee_code: str
    name: str
    area: Optional[float] = None
    population: Optional[int] = None
    region_insee_code: str
    capital_city_insee_code: Optional[str] = None


class DepartmentResponse(DepartmentCreate):
    class Config:
        from_attributes = True


class CityCreate(BaseModel):
    city_insee_code: str
    name: str
    zip_code: int
    latitude: Optional[float]
    longitude: Optional[float]
    area: Optional[float] = None
    population: Optional[int] = None
    department_insee_code: str


class CityResponse(CityCreate):
    class Config:
        from_attributes = True


class PropertyAdCreate(BaseModel):
    city_insee_code: str
    building_type: BuildingType
    is_rental: int
    price: float
    area: float
    publication_date: datetime
    rooms_count: Optional[int] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    energy_consumption: Optional[EnergyConsumption] = None
    ges: Optional[GES] = None


class PropertyAdResponse(PropertyAdCreate):
    id: int
    inserted_at: datetime

    class Config:
        from_attributes = True


# --- Monitoring database CRUD schemas --- #
class FetchingReportCreate(BaseModel):
    source_name: str
    fetch_type: int
    success: bool
    started_at: datetime
    ended_at: datetime
    duration_in_seconds: float
    item_processed_count: int


class FetchingReportResponse(FetchingReportCreate):
    id: int
    inserted_at: datetime

    class Config:
        from_attributes = True


class SchedulingReportCreate(BaseModel):
    success: bool
    started_at: datetime
    ended_at: datetime
    duration_in_seconds: float
    scheduled_ads_count: int


class SchedulingReportResponse(SchedulingReportCreate):
    id: int
    inserted_at: datetime

    class Config:
        from_attributes = True


class AnalysisReportCreate(BaseModel):
    success: bool
    started_at: datetime
    ended_at: datetime
    duration_in_seconds: float
    accepted: bool
    discard_reason: Optional[str] = None


class AnalysisReportResponse(AnalysisReportCreate):
    id: int
    inserted_at: datetime

    class Config:
        from_attributes = True
