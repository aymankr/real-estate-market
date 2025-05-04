from enum import Enum
from pyspark.sql.types import (
    StructType, StructField,
    StringType, FloatType,
    BooleanType, IntegerType,
    TimestampType,
)

class BuildingType(Enum):
    HOUSE     = 1
    APARTMENT = 2
    BUILDING  = 3
    LAND      = 4
    PARKING   = 5
    OFFICE    = 6
    SHOP      = 7
    WAREHOUSE = 8
    OTHER     = 9

SchemaPropertyAd = StructType([
    StructField("source_id", StringType(), True),
    StructField("building_type", StringType(), True),
    StructField("is_rent", BooleanType(), True),
    StructField("price", FloatType(), True),
    StructField("area", FloatType(), True),
    StructField("latitude", FloatType(), True),
    StructField("longitude", FloatType(), True),
    StructField("city_insee_code", StringType(), True),
    StructField("rooms_count", IntegerType(), True),
    StructField("energy_consumption", StringType(), True),
    StructField("ges", StringType(), True),
    StructField("publication_date", StringType(), True),
    StructField("last_seen", TimestampType(), True),
])
