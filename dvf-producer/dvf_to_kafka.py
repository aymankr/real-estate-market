#!/usr/bin/env python3
import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

from immo_viz_api.database import get_viz_db
from immo_viz_api.models import Department

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s – %(message)s")
logger = logging.getLogger("dvf-producer")

BOOTSTRAP_SERVERS        = os.getenv("KAFKA_HOST", "kafka:9092").split(",")
KAFKA_TOPIC              = os.getenv("KAFKA_TOPIC_NAME", "dvf-property-ads")
MAX_WORKERS              = int(os.getenv("DVF_PRODUCER_MAX_WORKERS", "10"))

GEO_COMMUNES_URL         = (
    "https://geo.api.gouv.fr/departements/{dept}/communes?"
    "geometry=contour&format=geojson&type=commune-actuelle"
)
CADASTRE_SECTIONS_URL    = (
    "https://cadastre.data.gouv.fr/bundler/cadastre-etalab/"
    "communes/{commune}/geojson/sections"
)
DVF_MUTATIONS_URL        = (
    "https://app.dvf.etalab.gouv.fr/api/mutations3/"
    "{commune}/{prefix}{code}?per_page=1000"
)

TYPE_LOCAL_MAP = {"Appartement": 1, "Maison": 2}

def ensure_topic():
    """Creates the topic if missing, retrying if Kafka is unavailable."""
    num_partitions     = int(os.getenv("DVF_KAFKA_PARTITIONS", "50"))
    replication_factor = int(os.getenv("DVF_KAFKA_RF", "1"))

    while True:
        try:
            admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
            existing = set(admin.list_topics())
            if KAFKA_TOPIC not in existing:
                admin.create_topics([
                    NewTopic(name=KAFKA_TOPIC,
                             num_partitions=num_partitions,
                             replication_factor=replication_factor)
                ])
                logger.info(f"Topic '{KAFKA_TOPIC}' created ({num_partitions} partitions, RF={replication_factor})")
            else:
                logger.info(f"Topic '{KAFKA_TOPIC}' already exists")
            admin.close()
            return
        except NoBrokersAvailable:
            logger.warning("Kafka unavailable, retrying in 5s…")
            time.sleep(5)
        except TopicAlreadyExistsError:
            return
        except Exception as e:
            logger.error("Error in ensure_topic()", exc_info=True)
            raise

def init_producer() -> KafkaProducer:
    """Initializes a KafkaProducer with retry."""
    while True:
        try:
            p = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode(),
                acks="all",
                retries=5,
                linger_ms=20,
                batch_size=32*1024
            )
            logger.info(f"✅ Producer connected to {BOOTSTRAP_SERVERS}")
            return p
        except NoBrokersAvailable:
            logger.warning("Kafka not available (init), retrying in 5s…")
            time.sleep(5)

def clean_val(x):
    if isinstance(x, str) and x.lower() in {"none", "nan"}:
        return None
    return x

def get_departments() -> List[Department]:
    sess = next(get_viz_db())
    try:
        return sess.query(Department).all()
    finally:
        sess.close()

def fetch_communes(dept: str, sess: requests.Session) -> List[str]:
    url = GEO_COMMUNES_URL.format(dept=dept)
    r = sess.get(url, timeout=30); r.raise_for_status()
    codes = [f["properties"]["code"] for f in r.json().get("features", [])]
    logger.info(f"[Dept {dept}] {len(codes)} communes")
    return codes

def fetch_sections(commune: str, sess: requests.Session) -> List[Dict[str,Any]]:
    url = CADASTRE_SECTIONS_URL.format(commune=commune)
    r = sess.get(url, timeout=30); r.raise_for_status()
    feats = r.json().get("features", [])
    logger.info(f"\t[Commune {commune}] {len(feats)} sections")
    return feats

def fetch_mutations(commune: str, sec: Dict[str,Any], sess: requests.Session) -> List[Dict[str,Any]]:
    props = sec.get("properties", {})
    prefix, code = props.get("prefixe") or "", props.get("code") or ""
    if not code:
        return []
    url = DVF_MUTATIONS_URL.format(commune=commune, prefix=prefix, code=code)
    for i in range(5):
        r = sess.get(url, timeout=60)
        if r.status_code == 429:
            wait = 2**i
            logger.warning(f"\t\t[{commune}/{prefix+code}] 429 → retry {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return []
        r.raise_for_status()
        muts = r.json().get("mutations", [])
        logger.info(f"\t\t[{commune}/{prefix+code}] {len(muts)} mutations")
        return muts
    logger.error(f"\t\t[{commune}/{prefix+code}] stopped after 5×429 retries")
    return []

def process_and_send(m: Dict[str,Any], commune: str, producer: KafkaProducer) -> int:
    try:
        price = float(clean_val(m.get("valeur_fonciere")) or 0)
        area  = float(clean_val(m.get("surface_reelle_bati")) or 0)
        rooms = int(float(clean_val(m.get("nombre_pieces_principales")) or 0))
        lat   = clean_val(m.get("latitude"))
        lon   = clean_val(m.get("longitude"))
        lat   = float(lat) if lat is not None else None
        lon   = float(lon) if lon is not None else None
    except Exception as e:
        logger.warning(f"Bad data {commune}: {e} → skip")
        return 0

    payload = {
        "source_id":        "dvf",
        "building_type":    TYPE_LOCAL_MAP.get(clean_val(m.get("type_local")), 1),
        "price":            price,
        "area":             area,
        "rooms_count":      rooms,
        "latitude":         lat,
        "longitude":        lon,
        "publication_date": clean_val(m.get("date_mutation")),
        "city_insee_code":  commune,
        "last_seen":        datetime.now(timezone.utc).isoformat()
    }
    fut = producer.send(KAFKA_TOPIC, payload)
    fut.add_callback(lambda md: logger.debug(f"Sent {md.topic}[{md.partition}]@{md.offset}"))
    fut.add_errback(lambda e: logger.error(f"Kafka send error: {e}"))
    return 1


def task_section(commune, sec, producer, sess):
    cnt = 0
    for m in fetch_mutations(commune, sec, sess):
        cnt += process_and_send(m, commune, producer)
    return cnt


def main():
    logger.info(f"▶ DVF→Kafka (workers={MAX_WORKERS})")
    ensure_topic()
    producer = init_producer()

    http_sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS,
        max_retries=3
    )
    http_sess.mount("http://", adapter)
    http_sess.mount("https://", adapter)

    total, tasks = 0, []
    with ThreadPoolExecutor(MAX_WORKERS) as exe:
        depts = get_departments()
        logger.info(f"{len(depts)} departments to be treated")
        for d in depts:
            cd = d.insee_code.zfill(2)
            try:
                communes = fetch_communes(cd, http_sess)
            except Exception as e:
                logger.error(f"[Dept {cd}] failed fetch_communes: {e}")
                continue
            for com in communes:
                try:
                    secs = fetch_sections(com, http_sess)
                except Exception as e:
                    logger.error(f"[Commune {com}] failed fetch_sections: {e}")
                    continue
                for sec in secs:
                    tasks.append(exe.submit(task_section, com, sec, producer, http_sess))

        logger.info(f"{len(tasks)} tasks, waiting…")
        for i, f in enumerate(as_completed(tasks), 1):
            try:
                total += f.result()
            except Exception as e:
                logger.error("DVF Error", exc_info=True)
            if i % 100 == 0:
                logger.info(f"{i}/{len(tasks)} completed, total messages={total}")

    producer.flush()
    producer.close()
    http_sess.close()
    logger.info(f"✓ Finished → {total} send messages")

if __name__ == "__main__":
    main()
