from datetime import datetime
from json import dumps as json_dumps

from requests import post as requests_post

from analysis_scheduler.providers.env_vars_provider import EnvVarsProvider
from analysis_scheduler.services.stats_controller import AnalysisSchedulingReport


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def send_scheduling_report(report: AnalysisSchedulingReport):
    api_url: str = f"{EnvVarsProvider().get_immo_viz_api_url()}/scheduling_reports"
    requests_post(url=api_url, data=json_dumps(report, default=serialize_datetime))
