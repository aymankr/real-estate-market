from typing import Optional
from pydantic import BaseModel


class RegionCreate(BaseModel):
    insee_code: str
    name: str
    area: Optional[float] = None
    population: Optional[int] = None
    capital_city_insee_code: Optional[str] = None


class RegionResponse(RegionCreate):
    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    insee_code: str
    name: str
    area: Optional[float] = None
    population: Optional[int] = None
    region_insee_code: str
    capital_city_insee_code: Optional[str] = None


class DepartmentResponse(DepartmentCreate):
    class Config:
        from_attributes = True


class CityCreate(BaseModel):
    insee_code: str
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
