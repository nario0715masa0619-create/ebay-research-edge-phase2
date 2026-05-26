from typing import List, Dict, Optional
import datetime
from src.incident.models.incident import Incident, IncidentStatus, IncidentSeverity, SlaState
from src.incident.models.incident_reports import IncidentSummary

class IncidentDashboardService:
    def __init__(self, incident_repo=None):
        self.incident_repo = incident_repo

    def get_incident_summary(self, time_range_hours: int = 24, filter_severity: Optional[str] = None, filter_seller: Optional[str] = None, filter_environment: Optional[str] = None) -> IncidentSummary:
        if not self.incident_repo:
            return IncidentSummary()
            
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=time_range_hours)
        incidents = self.incident_repo.get_incidents(since, filter_severity, filter_seller, filter_environment)
        
        summary = IncidentSummary()
        summary.by_severity = {s.value: 0 for s in IncidentSeverity}
        
        total_ack_time = 0
        total_res_time = 0
        ack_count = 0
        res_count = 0

        for inc in incidents:
            summary.by_severity[inc.severity.value] = summary.by_severity.get(inc.severity.value, 0) + 1
            
            if inc.seller_account_id:
                summary.by_seller[inc.seller_account_id] = summary.by_seller.get(inc.seller_account_id, 0) + 1
            if inc.environment:
                summary.by_environment[inc.environment] = summary.by_environment.get(inc.environment, 0) + 1
                
            if inc.incident_status == IncidentStatus.OPEN: summary.total_open += 1
            elif inc.incident_status == IncidentStatus.ACKNOWLEDGED: summary.total_ack += 1
            elif inc.incident_status == IncidentStatus.INVESTIGATING: summary.total_investigating += 1
            elif inc.incident_status == IncidentStatus.RESOLVED: summary.total_resolved += 1
            elif inc.incident_status == IncidentStatus.CLOSED: summary.total_closed += 1
            elif inc.incident_status == IncidentStatus.CANCELLED: summary.total_cancelled += 1
            
            if inc.incident_status in [IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING]:
                summary.open_count += 1
                
            if inc.sla_state in [SlaState.ACK_BREACHED, SlaState.RESOLVE_BREACHED, SlaState.BOTH_BREACHED]:
                summary.breached_count += 1
                
            if inc.acknowledged_at:
                total_ack_time += (inc.acknowledged_at - inc.opened_at).total_seconds()
                ack_count += 1
            if inc.resolved_at:
                total_res_time += (inc.resolved_at - inc.opened_at).total_seconds()
                res_count += 1

        if ack_count > 0:
            summary.mean_ack_time_hours = round(total_ack_time / 3600.0 / ack_count, 2)
        if res_count > 0:
            summary.mean_resolve_time_hours = round(total_res_time / 3600.0 / res_count, 2)
            
        # mock overdue count calculation for simple summary
        summary.overdue_count = len(self.get_overdue_incidents())
        
        return summary

    def get_open_incidents(self, sort_by: str = "opened_at", limit: int = 50) -> List[Incident]:
        if not self.incident_repo: return []
        incs = [i for i in self.incident_repo.get_all_incidents() if i.incident_status in [IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING]]
        if sort_by == "opened_at":
            incs.sort(key=lambda x: x.opened_at, reverse=True)
        return incs[:limit]

    def get_overdue_incidents(self) -> List[Incident]:
        if not self.incident_repo: return []
        now = datetime.datetime.utcnow()
        overdue = []
        for inc in self.get_open_incidents(limit=1000):
            is_ack_overdue = not inc.acknowledged_at and inc.ack_due_at and now > inc.ack_due_at
            is_res_overdue = not inc.resolved_at and inc.resolve_due_at and now > inc.resolve_due_at
            if is_ack_overdue or is_res_overdue:
                overdue.append(inc)
        return overdue

    def get_breached_incidents(self) -> List[Incident]:
        if not self.incident_repo: return []
        return [i for i in self.incident_repo.get_all_incidents() if i.sla_state in [SlaState.ACK_BREACHED, SlaState.RESOLVE_BREACHED, SlaState.BOTH_BREACHED]]

    def get_incidents_by_seller(self, seller_id: str, time_range_hours: int = 24) -> List[Incident]:
        if not self.incident_repo: return []
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=time_range_hours)
        return self.incident_repo.get_incidents(since, filter_seller=seller_id)

    def get_incidents_by_environment(self, environment: str, time_range_hours: int = 24) -> List[Incident]:
        if not self.incident_repo: return []
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=time_range_hours)
        return self.incident_repo.get_incidents(since, filter_environment=environment)

    def get_severity_distribution(self, time_range_hours: int = 24) -> Dict[str, int]:
        summary = self.get_incident_summary(time_range_hours)
        return summary.by_severity

    def get_mean_time_to_acknowledge(self, time_range_hours: int = 24) -> float:
        return self.get_incident_summary(time_range_hours).mean_ack_time_hours

    def get_mean_time_to_resolve(self, time_range_hours: int = 24) -> float:
        return self.get_incident_summary(time_range_hours).mean_resolve_time_hours
