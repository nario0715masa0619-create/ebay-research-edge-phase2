import pytest
import uuid
import datetime
from src.admin_cli.incident_commands import IncidentCLI, format_sla_badge, colorize_severity
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.models.incident_reports import IncidentSummary
from src.incident.models.incident_event import IncidentEvent, IncidentEventType
from src.incident.models.incident_link import IncidentLink, IncidentLinkEntityType

class MockDetectionService: pass
class MockManagementService:
    def __init__(self):
        self.called = []
    def acknowledge_incident(self, uid, actor, note): self.called.append(("ack", uid))
    def assign_incident(self, uid, owner, actor): self.called.append(("assign", uid, owner))
    def start_investigation(self, uid, actor, note): self.called.append(("inv", uid))
    def mitigate_incident(self, uid, actor, rc, note): self.called.append(("mit", uid, rc))
    def resolve_incident(self, uid, actor, note): self.called.append(("res", uid))
    def close_incident(self, uid, actor, note): self.called.append(("close", uid))
    def reopen_incident(self, uid, actor, reason): self.called.append(("reopen", uid))
    def cancel_incident(self, uid, actor, reason): self.called.append(("cancel", uid))

class MockDashboardService:
    def get_incident_summary(self, time_range_hours):
        return IncidentSummary(open_count=5, overdue_count=2, breached_count=1)
    def get_overdue_incidents(self):
        return [make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", overdue=True)]
    def get_breached_incidents(self):
        return [make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", breached=True)]

class MockLinkRepo:
    def __init__(self, links):
        self.links = links

class MockLinkingService:
    def __init__(self, repo):
        self.link_repo = repo

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

def make_inc(status, severity, seller, env, overdue=False, breached=False):
    inc = Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=severity,
        title="Test", summary="Test",
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
def cli():
    inc1 = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1")
    inc2 = make_inc(IncidentStatus.CLOSED, IncidentSeverity.LOW, "s2", "env1")
    repo = MockIncidentRepo([inc1, inc2])
    
    ev = IncidentEvent(uuid.uuid4(), inc1.incident_id, IncidentEventType.CREATED, "Test note", "sys", "sys")
    erepo = MockEventRepo([ev])
    
    lrepo = MockLinkRepo([IncidentLink(uuid.uuid4(), inc1.incident_id, IncidentLinkEntityType.SELLER, "s1")])
    linking = MockLinkingService(lrepo)
    
    return IncidentCLI(MockDetectionService(), MockManagementService(), MockDashboardService(), linking, repo, erepo)

# 1. scan
def test_scan(cli, capsys):
    assert cli.execute(["scan"]) == 0
    assert "Scanning" in capsys.readouterr().out

# 2. list all
def test_list_all(cli, capsys):
    assert cli.execute(["list"]) == 0
    out = capsys.readouterr().out
    assert "CRITICAL" in out
    assert "LOW" in out

# 3. list filter status
def test_list_status(cli, capsys):
    assert cli.execute(["list", "--status", "open"]) == 0
    out = capsys.readouterr().out
    assert "CRITICAL" in out
    assert "LOW" not in out

# 4. list filter severity
def test_list_severity(cli, capsys):
    assert cli.execute(["list", "--severity", "low"]) == 0
    out = capsys.readouterr().out
    assert "LOW" in out
    assert "CRITICAL" not in out

# 5. list filter seller
def test_list_seller(cli, capsys):
    assert cli.execute(["list", "--seller", "s2"]) == 0
    out = capsys.readouterr().out
    assert "LOW" in out
    assert "CRITICAL" not in out

# 6. list filter env
def test_list_env(cli, capsys):
    assert cli.execute(["list", "--environment", "env1"]) == 0
    out = capsys.readouterr().out
    assert "CRITICAL" in out

# 7. show valid
def test_show_valid(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["show", "--incident-id", str(inc.incident_id)]) == 0
    out = capsys.readouterr().out
    assert str(inc.incident_id) in out
    assert "Test note" in out

# 8. show invalid uuid
def test_show_invalid_uuid(cli, capsys):
    with pytest.raises(SystemExit):
        cli.execute(["show", "--incident-id", "bad"])

# 9. show not found
def test_show_not_found(cli, capsys):
    with pytest.raises(SystemExit):
        cli.execute(["show", "--incident-id", str(uuid.uuid4())])

# 10. acknowledge
def test_acknowledge(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["acknowledge", "--incident-id", str(inc.incident_id), "--note", "foo"]) == 0
    assert cli.management.called[0] == ("ack", inc.incident_id)

# 11. assign
def test_assign(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["assign", "--incident-id", str(inc.incident_id), "--owner", "user1"]) == 0
    assert cli.management.called[0] == ("assign", inc.incident_id, "user1")

# 12. investigate
def test_investigate(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["investigate", "--incident-id", str(inc.incident_id)]) == 0
    assert cli.management.called[0] == ("inv", inc.incident_id)

# 13. mitigate
def test_mitigate(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["mitigate", "--incident-id", str(inc.incident_id), "--root-cause", "RC1"]) == 0
    assert cli.management.called[0] == ("mit", inc.incident_id, "RC1")

# 14. resolve
def test_resolve(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["resolve", "--incident-id", str(inc.incident_id)]) == 0
    assert cli.management.called[0] == ("res", inc.incident_id)

# 15. close
def test_close(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["close", "--incident-id", str(inc.incident_id)]) == 0
    assert cli.management.called[0] == ("close", inc.incident_id)

# 16. reopen
def test_reopen(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["reopen", "--incident-id", str(inc.incident_id)]) == 0
    assert cli.management.called[0] == ("reopen", inc.incident_id)

# 17. cancel
def test_cancel(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["cancel", "--incident-id", str(inc.incident_id)]) == 0
    assert cli.management.called[0] == ("cancel", inc.incident_id)

# 18. dashboard
def test_dashboard(cli, capsys):
    assert cli.execute(["dashboard"]) == 0
    out = capsys.readouterr().out
    assert "Total Open: 5" in out

# 19. overdue
def test_overdue(cli, capsys):
    assert cli.execute(["overdue"]) == 0
    out = capsys.readouterr().out
    assert "s1" in out

# 20. breached
def test_breached(cli, capsys):
    assert cli.execute(["breached"]) == 0
    out = capsys.readouterr().out
    assert "s1" in out

# 21. links
def test_links(cli, capsys):
    inc = cli.repo.incs[0]
    assert cli.execute(["links", "--incident-id", str(inc.incident_id)]) == 0
    out = capsys.readouterr().out
    assert "seller" in out
    assert "s1" in out

# 22. missing required arg
def test_missing_arg(cli):
    assert cli.execute(["show"]) == 2 # argparse exit code 2

# 23. format_sla_badge
def test_format_sla_badge_overdue():
    inc = make_inc(IncidentStatus.OPEN, IncidentSeverity.CRITICAL, "s1", "env1", overdue=True)
    badge = format_sla_badge(inc)
    assert "ACK_OVERDUE" in badge

# 24. colorize_severity
def test_colorize_severity():
    c = colorize_severity("CRITICAL")
    assert "\033[91m" in c
