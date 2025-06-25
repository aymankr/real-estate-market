#!/usr/bin/env python3
import os
import json
import logging
import math
import random
import time
import sys
from datetime import datetime, timezone

import requests
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
from pyspark.sql import SparkSession

from models import BuildingType, EnergyConsumption

KAFKA_BOOTSTRAP = os.getenv("KAFKA_HOST", "kafka:9092")
TOPICS = os.getenv("KAFKA_ANALYZER_TOPICS", "dvf-property-ads,property-ads").split(",")
DVF_TOPIC = os.getenv("DVF_KAFKA_TOPIC", "dvf-property-ads")
API_URL = os.getenv("IMMO_VIZ_API_URL", "http://immo-viz-api:8000").rstrip("/")
SCRAPER_PARTITIONS = int(os.getenv("SCRAPER_KAFKA_PARTITIONS", "1"))
SCRAPER_RF = int(os.getenv("SCRAPER_KAFKA_RF", "1"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CHECKPOINT_LOCATION = os.getenv("CHECKPOINT_LOCATION", "/tmp/checkpoint_property_ads")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("analyzer")

_VALS    = [e.value for e in EnergyConsumption]
_e_cache = {}
_g_cache = {}

def pick_energy(city):
    if not city:
        log.debug("pick_energy: no city → None")
        return None
    if city not in _e_cache:
        _e_cache[city] = random.choice(_VALS)
    if random.random() < 0.75:
        return _e_cache[city]
    return random.choice(_VALS)

def pick_ges(city):
    if not city:
        return None
    if city not in _g_cache:
        _g_cache[city] = random.choice(_VALS)
    if random.random() < 0.75:
        return _g_cache[city]
    return random.choice(_VALS)

def post_to_api(endpoint, payload):
    try:
        url = f"{API_URL}/{endpoint}/"
        log.debug(f"POST {url} ← {payload}")
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        log.error(f"POST /{endpoint} failed: {e}")
        return False

def handle_dvf(rec):
    """Same code as the old consumer for DVF"""
    try:
        price = float(rec.get("price", 0))
        area  = float(rec.get("area", 0))
        rooms = int(rec.get("rooms_count", 0))
        btype = int(rec.get("building_type", 0))
    except Exception as e:
        log.warning(f"handle_dvf: bad types → skip ({e})")
        return False

    if not (200 < price < 10_000_000) or area <= 0 or rooms <= 0:
        return False
    if btype not in (BuildingType.HOUSE.value, BuildingType.APARTMENT.value):
        return False

    e = pick_energy(rec.get("city_insee_code"))
    g = pick_ges  (rec.get("city_insee_code"))
    if e is None or g is None:
        return False

    payload = {
        "city_insee_code":    rec["city_insee_code"],
        "building_type":      btype,
        "is_rental":          price <= 5000,
        "price":              price,
        "area":               area,
        "rooms_count":        rooms,
        "latitude":           rec.get("latitude"),
        "longitude":          rec.get("longitude"),
        "energy_consumption": e,
        "ges":                g,
        "publication_date":   datetime.now(timezone.utc).isoformat(),
        "inserted_at":        datetime.now(timezone.utc).isoformat(),
    }
    # cleaning non-finite floats
    for k, v in payload.items():
        if isinstance(v, float) and not math.isfinite(v):
            payload[k] = 0.0 if k in ("price", "area") else None
    return post_to_api("property_ads", payload)

def handle_scraper(rec):
    """Same code as the old consumer for 'property-ads' records"""
    bt = rec.get("building_type")
    if isinstance(bt, str) and bt in BuildingType.__members__:
        rec["building_type"] = BuildingType[bt].value

    rec["is_rental"] = rec.pop("is_rent", None)
    last = rec.pop("last_seen", None)
    pub  = rec.get("publication_date")
    if last:
        rec["publication_date"] = last.isoformat() if hasattr(last, "isoformat") else last
    elif hasattr(pub, "isoformat"):
        rec["publication_date"] = pub.isoformat()

    rec["inserted_at"] = datetime.now(timezone.utc).isoformat()

    if rec.get("energy_consumption") is None or rec.get("ges") is None:
        return False
    if not rec.get("building_type") or rec.get("is_rental") is None or not rec.get("publication_date"):
        log.warning("handle_scraper: missing required fields → skip")
        return False

    return post_to_api("property_ads", rec)

def wait_for_kafka(retries=30, delay=5):
    for i in range(retries):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
            admin.list_topics()
            admin.close()
            return True
        except NoBrokersAvailable:
            log.warning(f"Kafka unavailable, retry {i+1}/{retries}")
            time.sleep(delay)
    log.error("Kafka unreachable after retries")
    return False

def ensure_topics(partitions=SCRAPER_PARTITIONS, rf=SCRAPER_RF):
    admin    = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
    existing = set(admin.list_topics())
    to_create = []
    for t in TOPICS:
        if t not in existing:
            to_create.append(NewTopic(name=t, num_partitions=partitions, replication_factor=rf))
    if to_create:
        try:
            admin.create_topics(to_create)
            log.info(f"Created topics: {[t.name for t in to_create]}")
        except TopicAlreadyExistsError:
            pass
    admin.close()

def process_batch(df, epoch_id):
    batch_start = datetime.now(timezone.utc)

    rows = df.collect()
    total_count   = len(rows)
    success_count = 0
    failure_count = 0
    reasons       = set()

    for row in rows:
        log.debug(f"batch {epoch_id} ▶ {row.topic}@{row.partition}:{row.offset}")
        try:
            rec = json.loads(row.value)
        except Exception:
            failure_count += 1
            reasons.add("invalid_json")
            continue

        if row.topic == DVF_TOPIC:
            ok = handle_dvf(rec)
        else:
            ok = handle_scraper(rec)

        if ok:
            success_count += 1
        else:
            failure_count += 1
            # failure  due to missing fields or filter conditions
            if row.topic != DVF_TOPIC and (rec.get("energy_consumption") is None or rec.get("ges") is None):
                reasons.add("missing_fields")
            else:
                reasons.add("filter_conditions")

    batch_end = datetime.now(timezone.utc)
    duration = (batch_end - batch_start).total_seconds()
    accepted = success_count > 0
    discard_reason = None if accepted else ",".join(sorted(reasons)) or "no_records"

    # ssend analysis report per micro batch
    report = {
        "success": True,
        "started_at": batch_start.isoformat(),
        "ended_at": batch_end.isoformat(),
        "duration_in_seconds": duration,
        "accepted": accepted,
        "discard_reason": discard_reason
    }
    post_to_api("analysis_reports", report)
    log.info(f"Analysis report sent for batch {epoch_id}: "
             f"{success_count}/{total_count} accepted, reasons={discard_reason}")

if __name__ == "__main__":
    if not wait_for_kafka():
        sys.exit(1)

    ensure_topics()

    spark = (
        SparkSession.builder
            .appName("property-ads-analyzer")
            .config("spark.jars.ivy", os.getenv("SPARK_IVY_DIR", "/home/spark/.ivy2"))
            .config("spark.hadoop.hadoop.security.authentication", "simple")
            .config("spark.hadoop.hadoop.security.authorization", "false")
            .getOrCreate()
    )

    raw = (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
             .option("subscribe", ",".join(TOPICS))
             .option("startingOffsets", "latest")
             .load()
             .selectExpr("topic", "partition", "offset", "CAST(value AS STRING) as value")
    )

    (
        raw.writeStream
           .foreachBatch(process_batch)
           .option("checkpointLocation", CHECKPOINT_LOCATION)
           .start()
           .awaitTermination()
    )
