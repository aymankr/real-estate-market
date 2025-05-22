import os
import time
import json
import logging
import requests

from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from kafka.admin import KafkaAdminClient
from kafka.errors import NoBrokersAvailable, KafkaError

from models import SchemaPropertyAd, BuildingType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("property-ads-analyzer")

VIZ_API = os.getenv("IMMO_VIZ_API_URL").rstrip("/")
KAFKA_SERVERS = os.getenv("KAFKA_HOST").split(",")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_NAME")

def wait_for_kafka_topic(servers, topic, max_retries=20, retry_interval=15):
    """Poll Kafka until the topic exists (or give up)."""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Checking for Kafka topic '{topic}' (attempt {attempt}/{max_retries})")
            admin = KafkaAdminClient(bootstrap_servers=servers)
            if topic in admin.list_topics():
                logger.info(f"→ Topic '{topic}' is ready")
                admin.close()
                return True
            admin.close()
        except (NoBrokersAvailable, KafkaError) as e:
            logger.warning(f"Kafka unavailable: {e}")
        time.sleep(retry_interval)
    logger.error(f"✗ Kafka topic '{topic}' never appeared after {max_retries} tries")
    return False

def post_batch_to_api(df, batch_id):
    """
    Called once per micro-batch.  
    - Sends each record to /property_ads  
    - Emits a scheduling report to /analysis_reports  
    """
    # capture real batch window
    batch_start = datetime.now(timezone.utc)
    success_count = failure_count = 0

    # filter out records where energy_consumption or GES is null
    # filtered_df = df.filter(
    #     (col("energy_consumption").isNotNull()) & 
    #     (col("GES").isNotNull())
    # )

    # 1) push each ad
    for rec in df.toJSON().collect():
        try:
            payload = json.loads(rec)

            # map building_type from NAME→value
            bt = payload.get("building_type")
            if isinstance(bt, str) and bt in BuildingType.__members__:
                payload["building_type"] = BuildingType[bt].value

            # rename flags / dates
            payload["is_rental"] = payload.pop("is_rent", None)
            payload["publication_date"] = payload.pop("last_seen",
                                                      payload.get("publication_date"))

            # add insertion timestamp
            payload["inserted_at"] = datetime.now(timezone.utc).isoformat()

            # POST to immo-viz-api
            r = requests.post(f"{VIZ_API}/property_ads", json=payload, timeout=10)
            if 200 <= r.status_code < 300:
                success_count += 1
            else:
                failure_count += 1
                logger.error(f"POST /property_ads failed [{r.status_code}]: {r.text}")
        except Exception as e:
            failure_count += 1
            logger.error(f"Error processing record: {e}")

    # 2) send batch report
    batch_end = datetime.now(timezone.utc)
    report = {
        "success": (failure_count == 0),
        "started_at": batch_start.isoformat(),
        "ended_at":   batch_end.isoformat(),
        "duration_in_seconds": (batch_end - batch_start).total_seconds(),
        "accepted": (success_count > 0),
        "discard_reason": None if success_count > 0 else "All records failed processing"
    }

    try:
        r = requests.post(f"{VIZ_API}/analysis_reports", json=report, timeout=10)
        if not (200 <= r.status_code < 300):
            logger.error(f"POST /analysis_reports failed [{r.status_code}]: {r.text}")
        else:
            logger.info("✓ Analysis report sent successfully")
    except Exception as e:
        logger.error(f"Error sending analysis report: {e}")

    logger.info(f"Batch {batch_id}: {success_count} successes, {failure_count} failures")


def main():
    try:
        logger.info("▶ Starting property-ads-analyzer")

        logger.info("⟳ Waiting for Kafka topic…")
        if not wait_for_kafka_topic(KAFKA_SERVERS, KAFKA_TOPIC):
            logger.warning("Proceeding without confirmed Kafka topic")

        spark = (
            SparkSession.builder
            .appName("property-ads-analyzer")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.task.maxFailures", "10")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")

        # read raw JSON from Kafka
        raw = (
            spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", ",".join(KAFKA_SERVERS))
            .option("subscribe", KAFKA_TOPIC)
            .option("startingOffsets", "earliest")
            .option("failOnDataLoss", "false")
            .load()
        )

        # parse JSON → columns
        parsed = (
            raw.selectExpr("CAST(value AS STRING) AS json_str")
               .select(from_json(col("json_str"), SchemaPropertyAd).alias("ad"))
               .select("ad.*")
        )

        # dispatch each micro-batch
        query = (
            parsed.writeStream
                  .foreachBatch(post_batch_to_api)
                  .outputMode("append")
                  .trigger(processingTime="1 minute")
                  .start()
        )

        logger.info("✔ Streaming query started, awaiting termination")
        query.awaitTermination()

    except Exception as e:
        logger.error(f"💥 Fatal error in Spark job: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()