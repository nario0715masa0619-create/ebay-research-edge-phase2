import pytest
import uuid
import datetime
from flask import Flask
from src.admin_web.routes.incident_routes import incident_bp
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.models.incident_reports import IncidentSummary
from src.incident.models.incident_event import IncidentEvent, IncidentEventType
from src.incident.models.incident_link import IncidentLink, IncidentLinkEntityType
from src.incident.models.sla_policy import IncidentCandidate, IncidentCandidateType

class MockDashboardService:
    def get_incident_summary(self, time_range_hours):
        return IncidentSummary(open_count=5, overdue_count=2, breached_count=1)
    def get_open_incidents(self, limit):
        return []
    def get_overdue_incidents(self):
        return [make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", overdue=True)]
    def get_breached_incidents(self):
        return [make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", breached=True)]

class MockDetectionService:
    def detect_from_alert_burst(self):
        return [IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["s1"], 1.0, "reason")]

class MockManagementService:
    def __init__(self):
        self.called = []
    def acknowledge_incident(self, uid, actor, note): self.called.append(("ack", uid))
    def assign_incident(self, uid, owner, actor): self.called.append(("assign", uid, owner))
    def resolve_incident(self, uid, actor, note): self.called.append(("res", uid))
    def close_incident(self, uid, actor, note): self.called.append(("close", uid))
    def reopen_incident(self, uid, actor, reason): self.called.append(("reopen", uid))

class MockIncidentRepo:
    def __init__(self, incs):
        self.incs = incs
    def get_incident(self, uid):
        for i in self.incs:
            if i.incident_id == uid: return i
        raise Exception("Not found")
    def get_all_incidents(self):
        return self.incs

class MockEventRepo:
    def __init__(self, events):
        self.events = events

class MockLinkRepo:
    def __init__(self, links):
        self.links = links

def make_inc(status, severity, seller, env, overdue=False, breached=False):
    inc = Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=severity,
        title="Test Incident", summary="Test Summary",
        incident_status=status,
        sla_state=SlaState.BOTH_BREACHED if breached else SlaState.WITHIN_SLA,
        seller_account_id=seller,
        environment=env
    )
    now = datetime.datetime.utcnow()
    inc.opened_at = now - datetime.timedelta(hours=2)
    if overdue:
        inc.ack_due_at = now - datetime.timedelta(hours=1)
        inc.resolve_due_at = now + datetime.timedelta(hours=1)
    else:
        inc.ack_due_at = now + datetime.timedelta(hours=1)
        inc.resolve_due_at = now + datetime.timedelta(hours=4)
    return inc

@pytest.fixture
def app():
    app = Flask(__name__)
    
    inc1 = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1")
    inc2 = make_inc(IncidentStatus.CLOSED, IncidentSeverity.LOW, "s2", "env2")
    inc3 = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", overdue=True)
    inc4 = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", breached=True)
    repo = MockIncidentRepo([inc1, inc2, inc3, inc4])
    
    ev = IncidentEvent(uuid.uuid4(), inc1.incident_id, IncidentEventType.CREATED, "Test note", "sys", "sys")
    erepo = MockEventRepo([ev])
    
    lrepo = MockLinkRepo([IncidentLink(uuid.uuid4(), inc1.incident_id, IncidentLinkEntityType.SELLER, "s1")])
    
    incident_bp.dashboard_service = MockDashboardService()
    incident_bp.detection_service = MockDetectionService()
    incident_bp.management_service = MockManagementService()
    incident_bp.repo = repo
    incident_bp.event_repo = erepo
    incident_bp.link_repo = lrepo
    
    app.register_blueprint(incident_bp)
    
    # We mock render_template so we can just check context or html content
    # Actually, we don't need to mock it, we can just let it render if templates are in path.
    # To ensure it finds templates:
    import os
    app.template_folder = os.path.abspath('src/admin_web/templates')
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# 1. list incidents
def test_list_incidents(client):
    res = client.get('/ops/incidents/')
    assert res.status_code == 200
    assert b"Incident List" in res.data
    assert b"CRITICAL" in res.data

# 2. list filter status
def test_list_filter_status(client):
    res = client.get('/ops/incidents/?status=closed')
    assert res.status_code == 200
    assert b">LOW</span>" in res.data
    assert b">CRITICAL</span>" not in res.data

# 3. list filter severity
def test_list_filter_severity(client):
    res = client.get('/ops/incidents/?severity=low')
    assert res.status_code == 200
    assert b">LOW</span>" in res.data
    assert b">CRITICAL</span>" not in res.data

# 4. list filter seller
def test_list_filter_seller(client):
    res = client.get('/ops/incidents/?seller=s2')
    assert res.status_code == 200
    assert b"<td>s2</td>" in res.data
    assert b"<td>s1</td>" not in res.data

# 5. list filter environment
def test_list_filter_env(client):
    res = client.get('/ops/incidents/?environment=env2')
    assert res.status_code == 200
    assert b">LOW</span>" in res.data
    assert b">CRITICAL</span>" not in res.data

# 6. list filter overdue
def test_list_filter_overdue(client):
    res = client.get('/ops/incidents/?overdue=true')
    assert res.status_code == 200
    assert b"OVERDUE</span>" in res.data
    assert b"ON_TRACK</span>" not in res.data

# 7. list filter breached
def test_list_filter_breached(client):
    res = client.get('/ops/incidents/?breached=true')
    assert res.status_code == 200
    assert b"BREACHED</span>" in res.data
    assert b"ON_TRACK</span>" not in res.data

# 8. detail valid
def test_detail_valid(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.get(f'/ops/incidents/{uid}')
    assert res.status_code == 200
    assert b"Incident Detail" in res.data
    assert str(uid).encode() in res.data
    assert b"Test note" in res.data

# 9. detail not found
def test_detail_not_found(client):
    res = client.get(f'/ops/incidents/{uuid.uuid4()}')
    assert res.status_code == 404

# 10. detail invalid uuid
def test_detail_invalid_uuid(client):
    res = client.get('/ops/incidents/bad-uuid')
    assert res.status_code == 404

# 11. dashboard
def test_dashboard(client):
    res = client.get('/ops/incidents/dashboard')
    assert res.status_code == 200
    assert b"Incident Dashboard" in res.data
    assert b"Total Open" in res.data

# 12. overdue
def test_overdue(client):
    res = client.get('/ops/incidents/overdue')
    assert res.status_code == 200
    assert b"Overdue Incidents" in res.data
    assert b"CRITICAL" in res.data

# 13. breached
def test_breached(client):
    res = client.get('/ops/incidents/breached')
    assert res.status_code == 200
    assert b"Breached Incidents" in res.data

# 14. candidates
def test_candidates(client):
    res = client.get('/ops/incidents/candidates')
    assert res.status_code == 200
    assert b"Auto-Detected Candidates" in res.data
    assert b"CRITICAL" in res.data

# 15. acknowledge post
def test_acknowledge_post(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.post(f'/ops/incidents/{uid}/acknowledge', data={'note': 'test ack'})
    assert res.status_code == 302
    assert incident_bp.management_service.called[-1] == ("ack", uid)

# 16. assign post
def test_assign_post(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.post(f'/ops/incidents/{uid}/assign', data={'owner': 'user1'})
    assert res.status_code == 302
    assert incident_bp.management_service.called[-1] == ("assign", uid, "user1")

# 17. resolve post
def test_resolve_post(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.post(f'/ops/incidents/{uid}/resolve', data={'note': 'test res'})
    assert res.status_code == 302
    assert incident_bp.management_service.called[-1] == ("res", uid)

# 18. close post
def test_close_post(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.post(f'/ops/incidents/{uid}/close', data={'note': 'test cls'})
    assert res.status_code == 302
    assert incident_bp.management_service.called[-1] == ("close", uid)

# 19. reopen post
def test_reopen_post(client, app):
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    res = client.post(f'/ops/incidents/{uid}/reopen', data={'reason': 'test reopen'})
    assert res.status_code == 302
    assert incident_bp.management_service.called[-1] == ("reopen", uid)

# 20. exception handling in post (400)
def test_post_exception_handling(client, app):
    # force exception
    uid = app.blueprints['incident_bp'].repo.incs[0].incident_id
    def raise_err(*args, **kwargs): raise Exception("test error")
    app.blueprints['incident_bp'].management_service.acknowledge_incident = raise_err
    res = client.post(f'/ops/incidents/{uid}/acknowledge', data={'note': 'test'})
    assert res.status_code == 400
    assert b"test error" in res.data
