from enum import Enum
from typing import Optional, TypedDict


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


class PropertyAdItem(TypedDict):
    building_type: Enum
    is_rent: bool
    price: float
    area: float
    latitutde: Optional[float]
    longitude: Optional[float]
    rooms_count: Optional[int]
    energy_consumption: Optional[EnergyConsumption]
    ges: Optional[GES]
    city_insee_code: str
    publication_date: str
