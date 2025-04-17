from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from analysis_scheduler.providers.env_vars_provider import EnvVarsProvider


class MongoDBProvider(object):
    _client: MongoClient
    _fetch_db: Database
    _src_property_ads_collection: Collection
    _analysis_schedules_collection: Collection

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(MongoDBProvider, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        env_vars_provider = EnvVarsProvider()
        self._client = MongoClient(env_vars_provider.get_immo_fetch_mongo_uri())
        self._fetch_db = self._client[env_vars_provider.get_immo_fetch_mongo_db_name()]
        self._src_property_ads_collection = self._fetch_db[
            env_vars_provider.get_immo_fetch_mongo_collection_name()
        ]
        self._analysis_schedules_collection = self._fetch_db[
            env_vars_provider.get_analysis_schedules_collection_name()
        ]

    def get_client(self):
        return self._client

    def get_fetch_db(self):
        return self._fetch_db

    def get_src_property_ads_collection(self):
        return self._src_property_ads_collection
    
    def get_analysis_schedules_collection(self):
        return self._analysis_schedules_collection
