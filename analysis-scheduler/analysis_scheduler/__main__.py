import logging

from analysis_scheduler.daos.analysis_schedules_dao import (
    AnalysisSchedulesDAO,
)
from analysis_scheduler.daos.scr_property_ads_dao import (
    SourcePropertyAdDAO,
)
from analysis_scheduler.services.property_ads_analysis_launcher import (
    launch_ads_analysis_for_source,
    ensure_topic_exists,
)
from analysis_scheduler.services.scheduling_report_sender import send_scheduling_report
from analysis_scheduler.services.stats_controller import StatsController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def do_schedule(stats_controller: StatsController):
    ensure_topic_exists()
    
    logger.info("Getting the sources to possibly schedule...")
    last_seen_per_source = SourcePropertyAdDAO().get_last_seen_per_source()
    
    source_ids = [source[0] for source in last_seen_per_source]
    logger.info(f"Sources to possibly schedule: {', '.join(source_ids)}")

    for source_id, last_seen in last_seen_per_source:
        logger.info(f"Processing source id {source_id}...")
        last_analysis_schedule = AnalysisSchedulesDAO().get_by_source_id(source_id)
        
        if (last_analysis_schedule is not None and 
            last_analysis_schedule["last_schedule_date"] >= last_seen):
            logger.info(f"Last schedule date for source id {source_id} is up to date")
            stats_controller.record_up_to_date_source(
                source_id, SourcePropertyAdDAO().get_nb_ads_for_source(source_id)
            )
        else:
            logger.info(f"Last schedule date for source {source_id} is not up to date")
            logger.info(f"Launching property ads analysis for source {source_id}")
            
            success_count, failed_count = launch_ads_analysis_for_source(source_id)
            
            stats_controller.record_scheduled_source(
                source_id, success_count, failed_count
            )
            
            logger.info(
                f"{success_count} ads successfully scheduled for source {source_id}, "
                f"{failed_count} failed"
            )

def main():
    stats_controller = StatsController()
    stats_controller.start()
    logger.info(f"Analysis scheduler started at {stats_controller.started_at}")

    try:
        do_schedule(stats_controller)
        stats_controller.success = True
    except Exception as e:
        logger.error(f"Error during scheduling: {e}", exc_info=True)
        stats_controller.success = False
    finally:
        stats_controller.end()
        logger.info(f"Analysis scheduler ended at {stats_controller.ended_at}")

        scheduling_report = stats_controller.to_report()
        logger.info(f"Analysis report: {scheduling_report}")

        logger.info("Sending scheduling report to API...")
        send_scheduling_report(scheduling_report)
        logger.info("Scheduling report sent to API")

if __name__ == "__main__":
    main()
