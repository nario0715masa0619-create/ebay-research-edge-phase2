from typing import List, Dict, Any
import datetime
from src.incident.models.incident import Incident, IncidentStatus
from src.incident.models.incident_reports import IncidentDigestReport
from src.incident.services.incident_dashboard_service import IncidentDashboardService

class IncidentDigestService:
    def __init__(self, dashboard_service: IncidentDashboardService, incident_repo=None):
        self.dashboard = dashboard_service
        self.incident_repo = incident_repo

    def generate_overdue_digest(self, current_time: datetime.datetime = None) -> List[Incident]:
        return self.dashboard.get_overdue_incidents()

    def generate_breached_digest(self, current_time: datetime.datetime = None) -> List[Incident]:
        return self.dashboard.get_breached_incidents()

    def generate_daily_summary_digest(self, date: datetime.date) -> IncidentDigestReport:
        # Time range for the given date
        # Assuming we just use last 24h from midnight of that date (for simplicity here we just use the summary method)
        summary = self.dashboard.get_incident_summary(time_range_hours=24)
        
        top_severity = max(summary.by_severity.items(), key=lambda x: x[1])[0] if summary.by_severity else None
        
        report = IncidentDigestReport(
            period=str(date),
            report_type="daily_summary",
            incident_count=summary.total_open + summary.total_resolved + summary.total_closed + summary.total_cancelled,
            open_count=summary.open_count,
            resolved_count=summary.total_resolved,
            closed_count=summary.total_closed,
            overdue_count=summary.overdue_count,
            breached_count=summary.breached_count,
            top_issues={"top_severity": top_severity},
            recent_incidents=self.dashboard.get_open_incidents(limit=20)
        )
        return report

    def generate_severity_breakdown_digest(self, time_range_hours: int = 24) -> Dict[str, Any]:
        summary = self.dashboard.get_incident_summary(time_range_hours)
        return {
            "counts": summary.by_severity,
            "total_evaluated": sum(summary.by_severity.values())
        }

    def generate_repeated_incidents_digest(self, time_range_hours: int = 24) -> List[Incident]:
        if not self.incident_repo:
            return []
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=time_range_hours)
        incidents = self.incident_repo.get_incidents(since)
        
        # return incidents that are duplicates (cancelled and have duplicate_of_incident_id)
        repeated = [inc for inc in incidents if inc.incident_status == IncidentStatus.CANCELLED and inc.duplicate_of_incident_id is not None]
        return repeated
