from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from immoscraper.settings import (
    IMMO_FETCH_MONGO_COLLECTION_NAME,
    IMMO_FETCH_MONGO_DB_NAME,
    IMMO_FETCH_MONGO_URI,
)


class MongoDBProvider(object):
    _client: MongoClient
    _fetch_db: Database
    _src_property_ads_collection: Collection

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(MongoDBProvider, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._client = MongoClient(IMMO_FETCH_MONGO_URI)
        self._fetch_db = self._client[IMMO_FETCH_MONGO_DB_NAME]
        self._src_property_ads_collection = self._fetch_db[
            IMMO_FETCH_MONGO_COLLECTION_NAME
        ]

    def get_client(self):
        return self._client

    def get_fetch_db(self):
        return self._fetch_db

    def get_src_property_ads_collection(self):
        return self._src_property_ads_collection
