import pytest
import json
import os
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

from src.admin_cli.policy_commands import (
    scan, candidate_list, policy_list, show, propose, approve,
    activate, reject, release, expire, cancel, dashboard, digest,
    management_service, state_machine
)
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel, Severity
from src.ops_policy.models.ops_policy import OpsPolicy

class DummyArgs:
    def __init__(self, **kwargs):
        self.format = kwargs.get("format", "table")
        self.output_file = kwargs.get("output_file")
        self.dry_run = kwargs.get("dry_run", False)
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture(autouse=True)
def reset_management_service():
    # Clear out the dummy memory before each test
    management_service.policies.clear()
    management_service.events.clear()
    yield

def test_scan(capsys):
    args = DummyArgs()
    scan(args)
    captured = capsys.readouterr()
    assert "ID" in captured.out or "No data" in captured.out

def test_candidate_list_filtered(capsys):
    args = DummyArgs(severity="critical", limit=20)
    candidate_list(args)
    captured = capsys.readouterr()
    # It might be empty, just ensure it runs
    assert "No data" in captured.out or "ID" in captured.out

def test_policy_list_status(capsys):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    args = DummyArgs(status="proposed", scope=None, seller=None, env=None, limit=100)
    policy_list(args)
    captured = capsys.readouterr()
    assert "proposed" in captured.out

def test_policy_list_scope(capsys):
    management_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    args = DummyArgs(status=None, scope="seller", seller=None, env=None, limit=100)
    policy_list(args)
    captured = capsys.readouterr()
    assert "seller" in captured.out

def test_policy_list_pagination(capsys):
    for i in range(5):
        management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, f"T{i}", "R", "u")
    args = DummyArgs(status=None, scope=None, seller=None, env=None, limit=2)
    policy_list(args)
    captured = capsys.readouterr()
    # 2 rows + header
    assert len(captured.out.strip().split('\n')) == 3

def test_show_detail(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    args = DummyArgs(policy_id=str(p.policy_id))
    show(args)
    captured = capsys.readouterr()
    assert "=== POLICY DETAIL ===" in captured.out
    assert str(p.policy_id) in captured.out

def test_show_not_found():
    args = DummyArgs(policy_id=str(uuid4()))
    with pytest.raises(SystemExit) as e:
        show(args)
    assert e.value.code == 1

def test_propose_manual(capsys):
    args = DummyArgs(action="pause_handoff", scope="global", target=None, title="T", reason="R")
    propose(args)
    captured = capsys.readouterr()
    assert "policy_id" in captured.out

def test_approve(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    # By default, manual creates MEDIUM severity equiv which is OVERLAY, so review_due not strict
    p.level = PolicyLevel.OVERLAY 
    args = DummyArgs(policy_id=str(p.policy_id), review_due=None)
    approve(args)
    captured = capsys.readouterr()
    assert "approved" in captured.out

def test_approve_strong_requires_review_due():
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.BLOCK_LIVE_EXECUTION, "T", "R", "u")
    p.level = PolicyLevel.STRONG
    args = DummyArgs(policy_id=str(p.policy_id), review_due=None)
    with pytest.raises(SystemExit) as e:
        approve(args)
    assert e.value.code == 1

def test_activate(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p.status = PolicyStatus.APPROVED
    args = DummyArgs(policy_id=str(p.policy_id))
    activate(args)
    captured = capsys.readouterr()
    assert "active" in captured.out

def test_reject(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(policy_id=str(p.policy_id), reason="reject")
    reject(args)
    captured = capsys.readouterr()
    assert "rejected" in captured.out

def test_release(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p.status = PolicyStatus.ACTIVE
    args = DummyArgs(policy_id=str(p.policy_id))
    release(args)
    captured = capsys.readouterr()
    assert "released" in captured.out

def test_expire(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p.status = PolicyStatus.ACTIVE
    args = DummyArgs(policy_id=str(p.policy_id))
    expire(args)
    captured = capsys.readouterr()
    assert "expired" in captured.out

def test_cancel(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(policy_id=str(p.policy_id), reason="cancel")
    cancel(args)
    captured = capsys.readouterr()
    assert "cancelled" in captured.out

def test_invalid_transition():
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    # CANCELLED -> ACTIVE is invalid
    p.status = PolicyStatus.CANCELLED
    args = DummyArgs(policy_id=str(p.policy_id))
    with pytest.raises(SystemExit) as e:
        activate(args)
    assert e.value.code == 1

def test_dashboard_summary(capsys):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(seller=None, env=None)
    dashboard(args)
    captured = capsys.readouterr()
    assert "POLICY DASHBOARD" in captured.out
    assert "Total: 1" in captured.out

def test_digest_markdown(capsys):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p.status = PolicyStatus.ACTIVE
    args = DummyArgs(type="active", seller=None, env=None, date=None)
    digest(args)
    captured = capsys.readouterr()
    assert "# Active Operations Policies Digest" in captured.out
    assert "pause_handoff" in captured.out

def test_output_file(tmp_path):
    p = tmp_path / "out.txt"
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(status=None, scope=None, seller=None, env=None, limit=100, output_file=str(p))
    policy_list(args)
    assert p.exists()
    content = p.read_text()
    assert "PAUSE_HANDOFF" in content or "pause_handoff" in content

def test_format_json(capsys):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(status=None, scope=None, seller=None, env=None, limit=100, format="json")
    policy_list(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ACTION_TYPE"] == "pause_handoff"

def test_format_csv(capsys):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    args = DummyArgs(status=None, scope=None, seller=None, env=None, limit=100, format="csv")
    policy_list(args)
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert len(lines) == 2
    assert "POLICY_ID,ACTION_TYPE,SCOPE_TYPE,TARGET,STATUS,EFFECTIVE_FROM,REVIEW_DUE" in lines[0]
