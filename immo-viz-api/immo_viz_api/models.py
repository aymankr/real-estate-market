from enum import Enum
from sqlalchemy import Column, Integer, Float, String, Boolean, CHAR, DateTime
from immo_viz_api.database import VizBase, MonitoringBase

# --- Viz database models --- #
class Region(VizBase):
    __tablename__ = "regions"

    insee_code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    area = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)

    capital_city_insee_code = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Region(insee_code={self.insee_code}, name={self.name}, area={self.area}, population={self.population}) capital_city_insee_code={self.capital_city_insee_code})>"


class Department(VizBase):
    __tablename__ = "departments"

    insee_code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    area = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)

    region_insee_code = Column(String, nullable=False)
    capital_city_insee_code = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Department(insee_code={self.insee_code}, name={self.name}, region_insee_code={self.region_insee_code}, capital_city_insee_code={self.capital_city_insee_code})>"


class City(VizBase):
    __tablename__ = "cities"

    insee_code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    zip_code = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)

    department_insee_code = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<City(insee_code={self.insee_code}, name={self.name}, zip_code={self.zip_code} latitude={self.latitude}, longitude={self.longitude}, area={self.area}, population={self.population}, department_insee_code={self.department_insee_code})>"


class BuildingType(int, Enum):
    HOUSE = 1
    APARTMENT = 2
    BUILDING = 3
    LAND = 4
    PARKING = 5
    OFFICE = 6
    SHOP = 7
    WAREHOUSE = 8
    OTHER = 9


class EnergyConsumption(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class GES(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class PropertyAd(VizBase):
    __tablename__ = "property_ads"
    
    id = Column(Integer, primary_key=True, nullable=False)
    city_insee_code = Column(String, nullable=False)
    building_type = Column(Integer, nullable=False)
    is_rental = Column(Boolean, nullable=False)
    price = Column(Float, nullable=False)
    area = Column(Float, nullable=False)
    publication_date = Column(DateTime, nullable=False)
    rooms_count = Column(Integer, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    energy_consumption = Column(CHAR, nullable=True)
    ges = Column(CHAR, nullable=True)
    inserted_at = Column(DateTime, nullable=False)


# --- Monitoring database models --- #
class FetchType(int, Enum):
    SCRAP = 1
    API = 2
    XML = 3


class FetchingReport(MonitoringBase):
    __tablename__ = "fetching_reports"
    
    id = Column(Integer, primary_key=True, nullable=False)
    source_name = Column(String, nullable=False)
    fetch_type = Column(Integer, nullable=False)
    success = Column(Boolean, nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    duration_in_seconds = Column(Float, nullable=False)
    item_processed_count = Column(Integer, nullable=False)
    inserted_at = Column(DateTime, nullable=False)
