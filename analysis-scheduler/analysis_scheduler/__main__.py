from datetime import datetime

from analysis_scheduler.daos.analysis_schedules_dao import (
    AnalysisSchedulesDAO,
)
from analysis_scheduler.daos.scr_property_ads_dao import (
    SourcePropertyAdDAO,
)
from analysis_scheduler.services.property_ads_analysis_launcher import (
    launch_ads_analysis_for_source,
)
from analysis_scheduler.services.scheduling_report_sender import send_scheduling_report
from analysis_scheduler.services.stats_controller import StatsController


def main():
    # --- Start analysis scheduler --- #
    stats_controller: StatsController = StatsController()
    stats_controller.start()
    print(f"--- Analysis scheduler started at {stats_controller.started_at} ---")

    # --- Get the sources to possibly schedule --- #
    print("Getting the sources to possibly schedule...")
    last_seen_per_source: list[tuple[str, datetime]] = (
        SourcePropertyAdDAO().get_last_seen_per_source()
    )
    print(
        f"Sources to possibly schedule: {', '.join([source[0] for source in last_seen_per_source])}"
    )

    # --- Schedule the sources if not up to date --- #
    for source_id, last_seen in last_seen_per_source:
        print(f"Getting the last schedule date for source id {source_id}...")
        last_analysis_schedule = AnalysisSchedulesDAO().get_by_source_id(source_id)
        if (
            last_analysis_schedule is not None
            and last_analysis_schedule["last_schedule_date"] >= last_seen
        ):
            print(f"Last schedule date for source id {source_id} is up to date")
            stats_controller.record_up_to_date_source(
                source_id, SourcePropertyAdDAO().get_nb_ads_for_source(source_id)
            )
        else:
            print(f"Last schedule date for source {source_id} is not up to date")
            print(f"*** Launch property ads analysis for source {source_id} ***")
            successfull_analysis_launch, failed_analysis_launch = (
                launch_ads_analysis_for_source(source_id)
            )
            stats_controller.record_scheduled_source(
                source_id, successfull_analysis_launch, failed_analysis_launch
            )
            print(
                f"{successfull_analysis_launch} property ads analysis successfully scheduled for source {source_id}."
            )
            print(
                f"{failed_analysis_launch} property ads analysis failed to schedule for source {source_id}."
            )
        AnalysisSchedulesDAO().insert_one(source_id)

    # --- End analysis scheduler --- #
    stats_controller.end()
    print(f"--- Analysis scheduler ended at {stats_controller.ended_at} ---")

    # --- Send analysis report to API --- #
    report = stats_controller.to_report()
    print(f"-- Analysis report:\n{report} --")
    print("Sending analysis report to API...")
    send_scheduling_report(report)
    print("Analysis report sent to API")


if __name__ == "__main__":
    main()
