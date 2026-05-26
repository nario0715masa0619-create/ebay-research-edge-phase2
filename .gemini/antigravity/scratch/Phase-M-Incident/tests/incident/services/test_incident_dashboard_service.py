import pytest
import datetime
import uuid
from src.incident.services.incident_dashboard_service import IncidentDashboardService
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState

class MockIncidentRepo:
    def __init__(self, incidents):
        self.incidents = incidents
        
    def get_incidents(self, since, filter_severity=None, filter_seller=None, filter_environment=None):
        res = []
        for inc in self.incidents:
            if inc.opened_at >= since:
                if filter_severity and inc.severity != filter_severity: continue
                if filter_seller and inc.seller_account_id != filter_seller: continue
                if filter_environment and inc.environment != filter_environment: continue
                res.append(inc)
        return res
        
    def get_all_incidents(self):
        return self.incidents

def make_inc(status, severity, seller, env, hours_ago, ack_time=None, res_time=None, sla=SlaState.WITHIN_SLA):
    inc = Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=severity,
        title="Test", summary="Test",
        incident_status=status,
        sla_state=sla,
        seller_account_id=seller,
        environment=env
    )
    inc.opened_at = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_ago)
    inc.ack_due_at = inc.opened_at + datetime.timedelta(hours=1)
    inc.resolve_due_at = inc.opened_at + datetime.timedelta(hours=4)
    if ack_time:
        inc.acknowledged_at = inc.opened_at + datetime.timedelta(hours=ack_time)
    if res_time:
        inc.resolved_at = inc.opened_at + datetime.timedelta(hours=res_time)
    return inc

@pytest.fixture
def dashboard_service():
    incs = [
        make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", 2),
        make_inc(IncidentStatus.ACKNOWLEDGED, IncidentSeverity.HIGH, "s2", "env1", 5, ack_time=1),
        make_inc(IncidentStatus.RESOLVED, IncidentSeverity.MEDIUM, "s1", "env2", 10, ack_time=2, res_time=5),
        make_inc(IncidentStatus.CLOSED, IncidentSeverity.LOW, "s3", "env1", 20, ack_time=5, res_time=10),
        make_inc(IncidentStatus.CANCELLED, IncidentSeverity.LOW, "s1", "env1", 1)
    ]
    # One overdue open incident
    overdue_inc = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", 10)
    incs.append(overdue_inc)
    
    breached_inc = make_inc(IncidentStatus.RESOLVED, IncidentSeverity.CRITICAL, "s2", "env1", 10, ack_time=5, res_time=10, sla=SlaState.BOTH_BREACHED)
    incs.append(breached_inc)
    
    return IncidentDashboardService(MockIncidentRepo(incs))

# 11. get_incident_summary
def test_get_incident_summary(dashboard_service):
    summary = dashboard_service.get_incident_summary(time_range_hours=24)
    assert summary.total_open == 2
    assert summary.total_ack == 1
    assert summary.total_resolved == 2
    assert summary.total_closed == 1
    assert summary.total_cancelled == 1
    assert summary.open_count == 3
    assert summary.breached_count == 1
    assert summary.by_severity[IncidentSeverity.CRITICAL.value] == 3
    assert summary.by_seller["s1"] == 4
    assert summary.by_environment["env1"] == 6

# 12. get_open_incidents
def test_get_open_incidents(dashboard_service):
    open_incs = dashboard_service.get_open_incidents()
    assert len(open_incs) == 3 # 2 OPEN + 1 ACK

# 13. get_overdue_incidents
def test_get_overdue_incidents(dashboard_service):
    overdue = dashboard_service.get_overdue_incidents()
    # The one opened 10 hours ago but not acked is overdue
    # And the first one in list opened 2 hours ago is also overdue
    # And the ACKNOWLEDGED one opened 5 hours ago without resolution is also overdue
    assert len(overdue) == 3

# 14. get_breached_incidents
def test_get_breached_incidents(dashboard_service):
    breached = dashboard_service.get_breached_incidents()
    assert len(breached) == 1
    assert breached[0].sla_state == SlaState.BOTH_BREACHED

# 15. get_incidents_by_seller
def test_get_incidents_by_seller(dashboard_service):
    s1_incs = dashboard_service.get_incidents_by_seller("s1")
    assert len(s1_incs) == 4

# 16. get_incidents_by_environment
def test_get_incidents_by_environment(dashboard_service):
    env2_incs = dashboard_service.get_incidents_by_environment("env2")
    assert len(env2_incs) == 1

# 17. get_severity_distribution
def test_get_severity_distribution(dashboard_service):
    dist = dashboard_service.get_severity_distribution()
    assert dist[IncidentSeverity.CRITICAL.value] == 3

# 18. mean_time_to_acknowledge
def test_mean_time_to_acknowledge(dashboard_service):
    mean_ack = dashboard_service.get_mean_time_to_acknowledge()
    # Ack times: 1, 2, 5, 5 -> avg = 3.25
    assert mean_ack == 3.25

# 19. mean_time_to_resolve
def test_mean_time_to_resolve(dashboard_service):
    mean_res = dashboard_service.get_mean_time_to_resolve()
    # Res times: 5, 10, 10 -> avg = 8.33
    assert mean_res == 8.33
