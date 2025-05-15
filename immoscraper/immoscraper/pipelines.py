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
    latitude: Optional[float]
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
        property_id = f"{item['building_type'].name}-{item['price']}-{item['area']}"
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
        lat = item.get('latitude') or 'N/A'
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
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "rooms_count": item["rooms_count"],
                "energy_consumption": item["energy_consumption"].value if item["energy_consumption"] else None,
                "ges": item["ges"].value if item["ges"] else None,
                "city_insee_code": item["city_insee_code"],
                "publication_date": item["publication_date"],
            },
            "last_seen": datetime.utcnow()
        })


