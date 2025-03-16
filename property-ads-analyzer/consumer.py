import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.streaming import StreamingQuery
from datetime import datetime
from datetime import UTC as dt_UTC
import requests
from requests.models import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

spark: SparkSession = SparkSession.builder.appName("kafka-consumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
    .getOrCreate()

# Subscribe to 1 topic
df: DataFrame = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "topic1") \
    .load()

# Function to send data to REST API
def log_batch(batch_df: DataFrame, batch_id: int) -> None:
    logger.info(f"Processing batch {batch_id} at {start}")
    batch_df.show()
    

query: StreamingQuery = df \
    .writeStream \
    .outputMode("append") \
    .foreachBatch(log_batch) \
    .start()

query.awaitTermination()
