from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict

from analysis_scheduler.providers.mongodb_provider import MongoDBProvider


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


class SourcePropertyAd(TypedDict):
    source_id: str
    building_type: BuildingType
    is_rent: bool
    price: float
    area: float
    latitude: Optional[float]
    longitude: Optional[float]
    rooms_count: Optional[int]
    energy_consumption: Optional[EnergyConsumption]
    ges: Optional[GES]
    last_seen: datetime


class SourcePropertyAdDAO:
    def __init__(self):
        self._collection = MongoDBProvider().get_src_property_ads_collection()

    def get_last_seen_per_source(self) -> list[tuple[str, datetime]]:
        """Returns the last seen date for each source id."""
        # Group by source id and get the max last seen date
        pipeline = [
            {"$group": {"_id": "$source_id", "last_seen": {"$max": "$last_seen"}}}
        ]
        return [
            (doc["_id"], doc["last_seen"])
            for doc in self._collection.aggregate(pipeline)
        ]

    def get_nb_ads_for_source(self, source_id: str) -> int:
        """Returns the number of ads for a source."""
        return self._collection.count_documents({"source_id": source_id})

    def get_ads_for_source(self, source_id: str) -> list[dict]:
        from analysis_scheduler.daos.analysis_schedules_dao import AnalysisSchedulesDAO
        
        schedule_dao = AnalysisSchedulesDAO()
        schedule = schedule_dao.get_by_source_id(source_id)
        
        query = {"source_id": source_id}
        if schedule and schedule.get("last_schedule_date"):
            query["last_seen"] = {"$gt": schedule["last_schedule_date"]}
        
        return list(self._collection.find(query))
