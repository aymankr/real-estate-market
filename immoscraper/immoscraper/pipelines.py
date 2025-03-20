from datetime import datetime
from json import dumps as json_dumps
from logging import Logger
from typing import Optional, TypedDict

from pymongo.collection import Collection
from requests import post as post_request
from scrapy import Spider

from immoscraper.items import GES, BuildingType, EnergyConsumption, PropertyAdItem
from immoscraper.mongodb_provider import MongoDBProvider
from immoscraper.settings import IMMO_VIZ_API_URL


class SourcePropertyAdMongo(TypedDict):
    source_id: str
    building_type: BuildingType
    is_rent: bool
    price: float
    area: float
    latitutde: Optional[float]
    longitude: Optional[float]
    rooms_count: Optional[int]
    energy_consumption: Optional[EnergyConsumption]
    ges: Optional[GES]
    last_seen: datetime


class PropertyAdInserter(object):
    logger: Logger
    src_property_ads_collection: Collection

    def open_spider(self, spider: Spider):
        self.logger = Logger(spider.name)
        self.src_property_ads_collection = (
            MongoDBProvider().get_src_property_ads_collection()
        )

    def process_item(self, item: PropertyAdItem, spider: Spider):
        self.logger.info(f"Inserting item {item} into MongoDB")
        self.src_property_ads_collection.insert_one(
            SourcePropertyAdMongo(
                source_id=spider.name,
                building_type=item["building_type"],
                is_rent=item["is_rent"],
                price=item["price"],
                area=item["area"],
                latitutde=item["latitutde"],
                longitude=item["longitude"],
                rooms_count=item["rooms_count"],
                energy_consumption=item["energy_consumption"],
                ges=item["ges"],
                last_seen=datetime.now(),
            )
        )
        self.logger.info(f"Item {item} inserted into MongoDB")
        return item


class FetchingReport(TypedDict):
    source_name: str
    fetch_type: int
    success: bool
    started_at: datetime
    ended_at: datetime
    duration_in_seconds: float
    item_processed_count: int


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


class ScrapReporter(object):
    logger: Logger
    start_time: datetime
    end_time: datetime
    item_processed_count: int

    def open_spider(self, spider: Spider):
        self.logger = Logger(spider.name)
        self.start_time = datetime.now()
        self.item_processed_count = 0

    def process_item(self, item: PropertyAdItem, _spider: Spider):
        self.item_processed_count += 1
        return item

    def close_spider(self, spider: Spider):
        end_time = datetime.now()
        duration_in_seconds = (end_time - self.start_time).total_seconds()
        report = FetchingReport(
            source_name=spider.name,
            fetch_type=1,
            success=self.item_processed_count > 0,
            started_at=self.start_time,
            ended_at=end_time,
            duration_in_seconds=duration_in_seconds,
            item_processed_count=self.item_processed_count,
        )
        self.logger.info(f"Sending report {report} to API.")
        post_request(
            url=IMMO_VIZ_API_URL + "/fetching_reports",
            data=json_dumps(report, default=serialize_datetime),
        )
        self.logger.info(f"Report successfully {report} sent to API.")
