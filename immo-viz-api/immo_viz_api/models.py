from sqlalchemy import Column, Integer, Float, String
from immo_viz_api.database import VizBase


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
