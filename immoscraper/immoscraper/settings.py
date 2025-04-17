# Scrapy settings for immoscraper project
import os
from dotenv import load_dotenv

# Load environment variables from .env file if any
load_dotenv()

BOT_NAME = "immoscraper"

SPIDER_MODULES = ["immoscraper.spiders"]
NEWSPIDER_MODULE = "immoscraper.spiders"

ITEM_PIPELINES = {
    "immoscraper.pipelines.PropertyAdInserter": 100,
    "immoscraper.pipelines.ScrapReporter": 200,
}

IMMO_FETCH_MONGO_URI = os.getenv("IMMO_FETCH_MONGO_URI")
IMMO_FETCH_MONGO_DB_NAME = os.getenv("IMMO_FETCH_MONGO_DB_NAME")
IMMO_FETCH_MONGO_COLLECTION_NAME = os.getenv("IMMO_FETCH_MONGO_COLLECTION_NAME")

IMMO_VIZ_API_URL = os.getenv("IMMO_VIZ_API_URL")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")