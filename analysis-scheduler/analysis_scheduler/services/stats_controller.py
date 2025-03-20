from datetime import datetime
from typing import TypedDict


class AnalysisSchedulingReport(TypedDict):
    success: bool
    started_at: datetime
    ended_at: datetime
    duration_in_seconds: float
    scheduled_ads_count: int


class StatsController:
    success: bool
    started_at: datetime
    ended_at: datetime
    scheduled_sources: dict[str, tuple[int, int]]
    up_to_date_sources: dict[str, int]

    def __init__(self):
        self.scheduled_sources = dict()
        self.up_to_date_sources = dict()

    def start(self):
        self.started_at = datetime.now()

    def record_scheduled_source(
        self,
        source_id: str,
        successfull_analysis_launches: int,
        failed_analysis_launches: int,
    ):
        self.scheduled_sources[source_id] = (
            successfull_analysis_launches,
            failed_analysis_launches,
        )

    def record_up_to_date_source(self, source_id: str, up_to_date_ads_count: int):
        self.up_to_date_sources[source_id] = up_to_date_ads_count

    def get_scheduled_ads_count(self) -> int:
        return sum(
            [
                successfull_analysis_launches
                for successfull_analysis_launches, failed_analysis_launches in self.scheduled_sources.values()
            ]
        )

    def end(self):
        self.ended_at = datetime.now()

    def to_report(self) -> AnalysisSchedulingReport:
        scheduled_ads_count = self.get_scheduled_ads_count()
        return {
            "success": self.success,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_in_seconds": (self.ended_at - self.started_at).total_seconds(),
            "scheduled_ads_count": scheduled_ads_count,
        }
