#!/usr/bin/env python3
import os
import json
import logging
import math
import random
import time
import sys
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import requests

from models import BuildingType, EnergyConsumption

KAFKA_BOOTSTRAP   = os.getenv("KAFKA_HOST", "kafka:9092")
TOPICS           = os.getenv("KAFKA_ANALYZER_TOPICS", "dvf-property-ads,property-ads").split(",")
GROUP_ID         = os.getenv("KAFKA_CONSUMER_GROUP", "property-ads-analyzers")
API_URL          = os.getenv("IMMO_VIZ_API_URL", "http://immo-viz-api:8000").rstrip("/")
DVF_TOPIC        = os.getenv("DVF_KAFKA_TOPIC", "dvf-property-ads")
LOG_LEVEL        = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("analyzer")

###
# Give each city a globally stable energy value (75% of the time it's the same letter),
# but keep a small proportion (25%) of "random variance" so that,
# if you run the job multiple times, all the ads of the same city do not systematically have the same score.
###
_VALS = [e.value for e in EnergyConsumption]
_e_cache = {}
_g_cache = {}

def pick_energy(city):
    if not city:
        log.debug("pick_energy: no city provided, returning None")
        return None
    if city not in _e_cache:
        _e_cache[city] = random.choice(_VALS)
        log.debug(f"pick_energy: first assignment for city {city} = {_e_cache[city]}")
    if random.random() < 0.75:
        log.debug(f"pick_energy: using cached value {_e_cache[city]} for city {city}")
        return _e_cache[city]
    choice = random.choice(_VALS)
    log.debug(f"pick_energy: random variance for city {city} = {choice}")
    return choice

def pick_ges(city):
    if not city:
        log.debug("pick_ges: no city provided, returning None")
        return None
    if city not in _g_cache:
        _g_cache[city] = random.choice(_VALS)
        log.debug(f"pick_ges: first assignment for city {city} = {_g_cache[city]}")
    if random.random() < 0.75:
        log.debug(f"pick_ges: using cached value {_g_cache[city]} for city {city}")
        return _g_cache[city]
    choice = random.choice(_VALS)
    log.debug(f"pick_ges: random variance for city {city} = {choice}")
    return choice

def wait_for_kafka(retries=30, delay=5):
    for i in range(retries):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
            admin.list_topics()
            admin.close()
            log.info("Kafka broker is available")
            return True
        except NoBrokersAvailable:
            log.warning(f"Kafka unavailable, retry {i+1}/{retries}")
            time.sleep(delay)
    log.error("Kafka still unavailable after retries")
    return False

def ensure_topics(partitions=1, rf=1):
    admin    = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
    existing = set(admin.list_topics())
    to_create = []
    for t in TOPICS:
        if t not in existing:
            to_create.append(NewTopic(name=t, num_partitions=partitions, replication_factor=rf))
            log.info(f"ensure_topics: scheduling creation of topic {t}")
    if to_create:
        try:
            admin.create_topics(to_create)
            log.info(f"Created topics: {[t.name for t in to_create]}")
        except TopicAlreadyExistsError:
            log.warning("ensure_topics: topic already exists during creation race")
    else:
        log.info("ensure_topics: all topics already exist")
    admin.close()

def post_to_api(endpoint, payload):
    try:
        log.debug(f"POSTing to /{endpoint}: {payload}")
        r = requests.post(f"{API_URL}/{endpoint}/", json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"POST /{endpoint} succeeded")
        return True
    except Exception as e:
        log.error(f"POST /{endpoint} failed: {e}")
        return False

def handle_dvf(rec):
    log.debug(f"handle_dvf: received record {rec}")
    try:
        price = float(rec.get("price", 0))
        area  = float(rec.get("area", 0))
        rooms = int(rec.get("rooms_count", 0))
        btype = int(rec.get("building_type", 0))
    except Exception as e:
        log.warning(f"handle_dvf: invalid types, skipping record: {e}")
        return False

    if not (200 < price < 10_000_000):
        log.debug(f"handle_dvf: price {price} out of bounds, skipping")
        return False
    if area <= 0:
        log.debug(f"handle_dvf: area {area} invalid, skipping")
        return False
    if rooms <= 0:
        log.debug(f"handle_dvf: rooms_count {rooms} invalid, skipping")
        return False
    if btype not in (BuildingType.HOUSE.value, BuildingType.APARTMENT.value):
        log.debug(f"handle_dvf: building_type {btype} not house/apartment, skipping")
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
        "energy_consumption": pick_energy(rec["city_insee_code"]),
        "ges":                pick_ges(rec["city_insee_code"]),
        "publication_date":   datetime.now(timezone.utc).isoformat(),
        "inserted_at":        datetime.now(timezone.utc).isoformat(),
    }
    for k, v in payload.items():
        if isinstance(v, float) and not math.isfinite(v):
            payload[k] = 0.0 if k in ("price", "area") else None
            log.debug(f"handle_dvf: cleaned non-finite {k} to {payload[k]}")

    return post_to_api("property_ads", payload)

def handle_scraper(rec):
    log.debug(f"handle_scraper: received record {rec}")
    bt = rec.get("building_type")
    if isinstance(bt, str) and bt in BuildingType.__members__:
        rec["building_type"] = BuildingType[bt].value
        log.debug(f"handle_scraper: mapped building_type '{bt}' to {rec['building_type']}")

    rec["is_rental"] = rec.pop("is_rent", None)
    last = rec.pop("last_seen", None)
    pub  = rec.get("publication_date")
    if last:
        rec["publication_date"] = last.isoformat() if hasattr(last, "isoformat") else last
        log.debug(f"handle_scraper: used last_seen for publication_date: {rec['publication_date']}")
    elif hasattr(pub, "isoformat"):
        rec["publication_date"] = pub.isoformat()
        log.debug(f"handle_scraper: formatted publication_date: {rec['publication_date']}")

    rec["inserted_at"] = datetime.now(timezone.utc).isoformat()
    log.debug(f"handle_scraper: set inserted_at to {rec['inserted_at']}")

    if not rec.get("building_type") or rec.get("is_rental") is None or not rec.get("publication_date"):
        log.warning("handle_scraper: missing required fields, skipping record")
        return False

    return post_to_api("property_ads", rec)

if __name__ == "__main__":
    if not wait_for_kafka():
        log.error("Kafka unreachable, exiting")
        sys.exit(1)
    ensure_topics(
        partitions=int(os.getenv("SCRAPER_KAFKA_PARTITIONS", "1")),
        rf=int(os.getenv("SCRAPER_KAFKA_RF", "1"))
    )

    try:
        consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=GROUP_ID,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8"))
        )
        log.info(f"Consuming topics {TOPICS} as group '{GROUP_ID}'")
    except Exception as e:
        log.error(f"Failed to create KafkaConsumer: {e}")
        sys.exit(1)

    for msg in consumer:
        log.info(f"Received message from topic '{msg.topic}', partition {msg.partition}, offset {msg.offset}")
        rec = msg.value
        if msg.topic == DVF_TOPIC:
            success = handle_dvf(rec)
            log.info(f"handle_dvf processed record: success={success}")
        else:
            success = handle_scraper(rec)
            log.info(f"handle_scraper processed record: success={success}")
