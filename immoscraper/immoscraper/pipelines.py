from datetime import datetime
from logging import Logger, getLogger
from typing import Optional, TypedDict
from scrapy import Spider

from immoscraper.items import GES, BuildingType, EnergyConsumption, PropertyAdItem
from immoscraper.mongodb_provider import MongoDBProvider


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
    city_insee_code: str
    publication_date: str
    last_seen: datetime


class PropertyAdInserter(object):
    logger: Logger

    def open_spider(self, spider: Spider):
        self.logger = getLogger(f"{spider.name}.PropertyAdInserter")
        self.logger.info("Opening MongoDB connection")
        
        try:
            self.src_property_ads_collection = (
                MongoDBProvider().get_src_property_ads_collection()
            )
            
            # Clear previous entries for this source
            # TODO: check if this is needed
            delete_result = self.src_property_ads_collection.delete_many({"source_id": spider.name})
            self.logger.info(f"Cleared {delete_result.deleted_count} previous items for source: {spider.name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    def process_item(self, item: PropertyAdItem, spider: Spider):
        property_id = item.get('source_id') or item.get('reference') # TODO check if id should be source_id or reference, or generated
        self.logger.info(f"Processing item: {property_id}")
        
        try:
            self._log_item(item)
            self._insert_item(item, spider)
            self.logger.info(f"Successfully stored item {property_id} in MongoDB")
        except Exception as e:
            self.logger.error(f"Failed to store item {property_id}: {str(e)}")
        
        return item
    
    def _log_item(self, item: PropertyAdItem):
        """Log item details including geolocation and timestamp."""
        lat = item.get('latitutde') or 'N/A'
        lon = item.get('longitude') or 'N/A'
        self.logger.info(
            "Item details: "
            f"{item['building_type'].name} | "
            f"{'Rental' if item['is_rent'] else 'Sale'} | "
            f"Price: {item['price']} | "
            f"Area: {item['area']}m² | "
            f"Rooms: {item['rooms_count'] or 'N/A'} | "
            f"Lat: {lat} | Lon: {lon} | "
            f"Location: {item['city_insee_code']} | "
            f"Energy: {item['energy_consumption'].value if item['energy_consumption'] else 'N/A'} | "
            f"GES: {item['ges'].value if item['ges'] else 'N/A'}"
        )
    
    def _insert_item(self, item: PropertyAdItem, spider: Spider):
        """Insert item into MongoDB"""
        self.src_property_ads_collection.insert_one({
            "source_id": spider.name,
            "property_ad_data": {
                "building_type": item["building_type"].name,
                "is_rent": item["is_rent"],
                "price": item["price"],
                "area": item["area"],
                "latitude": item["latitutde"],
                "longitude": item["longitude"],
                "rooms_count": item["rooms_count"],
                "energy_consumption": item["energy_consumption"].value if item["energy_consumption"] else None,
                "ges": item["ges"].value if item["ges"] else None,
                "city_insee_code": item["city_insee_code"],
                "publication_date": item["publication_date"],
            },
            "last_seen": datetime.utcnow()
        })


# ScrapReporter is replaced by FetchingReporterExtension
# see immoscraper/extensions.py

# class FetchingReport(TypedDict):
#     source_name: str
#     fetch_type: int
#     success: bool
#     started_at: datetime
#     ended_at: datetime
#     duration_in_seconds: float
#     item_processed_count: int


# def serialize_datetime(obj):
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     raise TypeError("Type not serializable")
# class ScrapReporter(object):
#     logger: Logger
#     item_processed_count: int = 0

#     def open_spider(self, spider: Spider):
#         self.logger = getLogger(f"{spider.name}.ScrapReporter")
#         self.start_time = datetime.now()
#         self.item_processed_count = 0
#         self.logger.info(f"Starting scraping at {self.start_time.isoformat()}")

#     def process_item(self, item: PropertyAdItem, _spider: Spider):
#         self.item_processed_count += 1
#         # Log every 10 items or the first one
#         if self.item_processed_count == 1 or self.item_processed_count % 10 == 0:
#             self.logger.info(f"Processed {self.item_processed_count} items so far")
#         return item

#     def close_spider(self, spider: Spider):
#         end_time = datetime.now()
#         duration_in_seconds = (end_time - self.start_time).total_seconds()
        
#         self.logger.info(
#             f"Scraping completed: {self.item_processed_count} items in {duration_in_seconds:.2f} seconds "
#             f"({self.item_processed_count / max(1, duration_in_seconds):.2f} items/sec)"
#         )
        
#         # Prepare report
#         report = FetchingReport(
#             source_name=spider.name,
#             fetch_type=1,
#             success=self.item_processed_count > 0,
#             started_at=self.start_time,
#             ended_at=end_time,
#             duration_in_seconds=duration_in_seconds,
#             item_processed_count=self.item_processed_count,
#         )
        
#         # Try to send report to API, but don't fail the spider if API is unavailable
#         try:
#             self.logger.info(f"Sending report to API with {self.item_processed_count} items")
            
#             response = post_request(
#                 url=IMMO_VIZ_API_URL + "/fetching_reports",
#                 data=json_dumps(report, default=serialize_datetime),
#                 timeout=10,  # Add timeout to prevent long waiting
#             )
            
#             if response.status_code == 200:
#                 self.logger.info(f"Report successfully sent to API: {response.status_code}")
#             else:
#                 self.logger.warning(f"API returned non-200 status code: {response.status_code}")
                
#         except request_exceptions.ConnectionError:
#             self.logger.warning(
#                 f"Could not connect to API at {IMMO_VIZ_API_URL}. "
#                 "This is normal if the API is not yet running - the report will be sent later."
#             )
#         except Exception as e:
#             self.logger.error(f"Error sending report to API: {str(e)}")
            
#         self.logger.info(f"Spider {spider.name} completed successfully with {self.item_processed_count} items")
