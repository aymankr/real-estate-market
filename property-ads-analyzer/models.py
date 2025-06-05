from enum import Enum

class BuildingType(Enum):
    HOUSE     = 1
    APARTMENT = 2
    BUILDING  = 3
    LAND      = 4
    PARKING   = 5
    OFFICE    = 6
    SHOP      = 7
    WAREHOUSE = 8
    OTHER     = 9

class EnergyConsumption(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

class GES(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

SchemaPropertyAd = {
    "source_id":         str,
    "building_type":     (str, int),
    "is_rent":           bool,
    "price":             (float, int),
    "area":              (float, int),
    "latitude":          (float, int, type(None)),
    "longitude":         (float, int, type(None)),
    "city_insee_code":   str,
    "rooms_count":       int,
    "energy_consumption": str,
    "ges":               str,
    "publication_date":  str,
    "last_seen":         str,
}
