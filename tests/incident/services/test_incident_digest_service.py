import pytest
import datetime
import uuid
from src.incident.services.incident_digest_service import IncidentDigestService
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus

class MockDashboardService:
    def __init__(self, summary, overdue, breached, open_incs):
        self.summary = summary
        self.overdue = overdue
        self.breached = breached
        self.open_incs = open_incs

    def get_incident_summary(self, time_range_hours):
        return self.summary
    def get_overdue_incidents(self):
        return self.overdue
    def get_breached_incidents(self):
        return self.breached
    def get_open_incidents(self, sort_by="opened_at", limit=50):
        return self.open_incs

class MockIncidentRepo:
    def __init__(self, incidents):
        self.incidents = incidents
    def get_incidents(self, since):
        return self.incidents

@pytest.fixture
def digest_service():
    from src.incident.models.incident_reports import IncidentSummary
    summary = IncidentSummary(
        total_open=2, total_resolved=5, total_closed=3, total_cancelled=1,
        open_count=3, overdue_count=1, breached_count=2,
        by_severity={IncidentSeverity.CRITICAL.value: 2, IncidentSeverity.HIGH.value: 8}
    )
    inc = Incident(incident_id=uuid.uuid4(), incident_type=IncidentType.SYSTEM_ERROR, severity=IncidentSeverity.HIGH, title="T", summary="T", incident_status=IncidentStatus.OPEN, sla_state="within")
    
    dup_inc = Incident(incident_id=uuid.uuid4(), incident_type=IncidentType.SYSTEM_ERROR, severity=IncidentSeverity.HIGH, title="D", summary="D", incident_status=IncidentStatus.CANCELLED, sla_state="within")
    dup_inc.duplicate_of_incident_id = uuid.uuid4()
    
    repo = MockIncidentRepo([inc, dup_inc])
    dash = MockDashboardService(summary, [inc], [inc, inc], [inc, inc])
    return IncidentDigestService(dash, repo)

# 20. generate_overdue_digest
def test_generate_overdue_digest(digest_service):
    digest = digest_service.generate_overdue_digest()
    assert len(digest) == 1

# 21. generate_breached_digest
def test_generate_breached_digest(digest_service):
    digest = digest_service.generate_breached_digest()
    assert len(digest) == 2

# 22. generate_daily_summary_digest
def test_generate_daily_summary_digest(digest_service):
    report = digest_service.generate_daily_summary_digest(datetime.date(2023, 1, 1))
    assert report.report_type == "daily_summary"
    assert report.incident_count == 11 # 2+5+3+1
    assert report.open_count == 3
    assert report.top_issues["top_severity"] == IncidentSeverity.HIGH.value
    assert len(report.recent_incidents) == 2

# 23. generate_severity_breakdown_digest
def test_generate_severity_breakdown_digest(digest_service):
    breakdown = digest_service.generate_severity_breakdown_digest()
    assert breakdown["total_evaluated"] == 10
    assert breakdown["counts"][IncidentSeverity.CRITICAL.value] == 2

# 24. generate_repeated_incidents_digest
def test_generate_repeated_incidents_digest(digest_service):
    repeated = digest_service.generate_repeated_incidents_digest()
    assert len(repeated) == 1
    assert repeated[0].incident_status == IncidentStatus.CANCELLED
    assert repeated[0].duplicate_of_incident_id is not None

# 25. daily_summary empty gracefully handles top_severity
def test_daily_summary_empty():
    from src.incident.models.incident_reports import IncidentSummary
    dash = MockDashboardService(IncidentSummary(), [], [], [])
    svc = IncidentDigestService(dash)
    rep = svc.generate_daily_summary_digest(datetime.date.today())
    assert rep.top_issues["top_severity"] is None

# 26. repeated_incidents without repo
def test_repeated_incidents_no_repo():
    dash = MockDashboardService(None, [], [], [])
    svc = IncidentDigestService(dash)
    assert len(svc.generate_repeated_incidents_digest()) == 0
