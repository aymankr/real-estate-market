# Scrapy settings for immoscraper project
import os

BOT_NAME = "immoscraper"

SPIDER_MODULES = ["immoscraper.spiders"]
NEWSPIDER_MODULE = "immoscraper.spiders"

ITEM_PIPELINES = {}

IMMO_VIZ_API_URL = os.getenv("IMMO_VIZ_API_URL")

KAFKA_HOST = os.getenv("KAFKA_HOST")