from datetime import datetime
from typing import TypedDict

from analysis_scheduler.providers.mongodb_provider import MongoDBProvider


class AnalysisSchedule(TypedDict):
    source_id: str
    last_schedule_date: datetime


class AnalysisSchedulesDAO:
    def __init__(self):
        self._collection = MongoDBProvider().get_analysis_schedules_collection()

    def get_by_source_id(self, source_id: str) -> AnalysisSchedule | None:
        mongo_doc = self._collection.find_one(
            {"source_id": source_id}, sort=[("last_schedule_date", -1)]
        )
        if mongo_doc is None:
            return None
        return AnalysisSchedule(**mongo_doc)

    def insert_one(self, source_id: str, last_schedule_date: datetime):
        self._collection.insert_one(
            AnalysisSchedule(
                source_id=source_id,
                last_schedule_date=last_schedule_date
            )
        )
