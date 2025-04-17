import os


class EnvVarsProvider(object):
    _immo_fetch_mongo_uri: str
    _immo_fetch_mongo_db_name: str
    _immo_fetch_mongo_collection_name: str
    _analysis_schedules_collection_name: str
    
    _kafka_host: str

    _immo_viz_api_url: str

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(EnvVarsProvider, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        try:
            self._immo_fetch_mongo_uri = os.environ["IMMO_FETCH_MONGO_URI"]
            self._immo_fetch_mongo_db_name = os.environ["IMMO_FETCH_MONGO_DB_NAME"]
            self._immo_fetch_mongo_collection_name = os.environ[
                "IMMO_FETCH_MONGO_COLLECTION_NAME"
            ]
            self._analysis_schedules_collection_name = os.environ[
                "ANALYSIS_SCHEDULES_COLLECTION_NAME"
            ]
            self._kafka_host = os.environ["KAFKA_HOST"]
            self._immo_viz_api_url = os.environ["IMMO_VIZ_API_URL"]
        except KeyError as e:
            raise KeyError(f"Environment variable {e} not set")

    def get_immo_fetch_mongo_uri(self):
        return self._immo_fetch_mongo_uri

    def get_immo_fetch_mongo_db_name(self):
        return self._immo_fetch_mongo_db_name

    def get_immo_fetch_mongo_collection_name(self):
        return self._immo_fetch_mongo_collection_name

    def get_analysis_schedules_collection_name(self):
        return self._analysis_schedules_collection_name

    def get_kafka_host(self):
        return self._kafka_host

    def get_immo_viz_api_url(self):
        return self._immo_viz_api_url
