from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
import json
from typing import Tuple, List
import logging

from analysis_scheduler.daos.scr_property_ads_dao import SourcePropertyAdDAO
from analysis_scheduler.daos.analysis_schedules_dao import AnalysisSchedulesDAO
from analysis_scheduler.providers.env_vars_provider import EnvVarsProvider

logger = logging.getLogger(__name__)

def ensure_topic_exists(bootstrap_servers: List[str] = None, topic_name: str = None, num_partitions: int = 1, replication_factor: int = 1):
    if bootstrap_servers is None:
        bootstrap_servers = EnvVarsProvider().get_kafka_bootstrap_servers()
    if topic_name is None:
        topic_name = EnvVarsProvider().get_kafka_topic_name()
        
    admin_client = None
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        
        topics = admin_client.list_topics()
        if topic_name in topics:
            logger.debug(f"Topic '{topic_name}' already exists")
            return
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )
        admin_client.create_topics([topic])
        logger.info(f"Created topic '{topic_name}'")
    except TopicAlreadyExistsError:
        logger.debug(f"Topic '{topic_name}' already exists (race condition)")
    except KafkaError as e:
        logger.warning(f"Failed to ensure topic exists: {e}")
    finally:
        if admin_client:
            admin_client.close()

def launch_ads_analysis_for_source(source_id: str) -> Tuple[int, int]:
    """
    Retrieve property ads for a given source and send them to Kafka topic.
    
    Args:
        source_id: The source identifier

    Returns:
        A tuple (number of ads successfully sent, number of failures)
    """
    bootstrap_servers = EnvVarsProvider().get_kafka_bootstrap_servers()
    topic_name = EnvVarsProvider().get_kafka_topic_name()
    
    ensure_topic_exists(bootstrap_servers, topic_name)
    
    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            acks='all'
        )
        
        ads_dao = SourcePropertyAdDAO()
        ads = ads_dao.get_ads_for_source(source_id)
        
        success, failure = 0, 0
        for ad in ads:
            try:
                payload = {
                    "source_id": ad["source_id"],
                    "last_seen": ad["last_seen"]
                }
                
                if "property_ad_data" in ad:
                    for key, value in ad["property_ad_data"].items():
                        payload[key] = value
                
                producer.send(topic_name, payload)
                success += 1
                logger.debug(f"Sent ad {ad.get('_id', 'unknown')} to Kafka")
            except Exception as e:
                logger.error(f"Error sending ad {ad.get('_id', 'unknown')} to Kafka: {e}")
                failure += 1
        
        producer.flush(timeout=10)
        
        if success > 0:
            schedules_dao = AnalysisSchedulesDAO()
            schedules_dao.insert_one(source_id)
            logger.info(f"Recorded scheduling for source {source_id}: {success} sent, {failure} failed")
        
        return success, failure
    except Exception as e:
        logger.error(f"Fatal error sending ads for source {source_id}: {e}")
        return 0, len(ads) if 'ads' in locals() else 0
    finally:
        if producer:
            producer.flush(timeout=10)
            producer.close(timeout=5)