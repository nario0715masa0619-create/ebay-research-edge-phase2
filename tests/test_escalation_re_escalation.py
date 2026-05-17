import pytest
from datetime import datetime, timedelta
from src.escalation.models import EscalationState, EscalationPolicy
from src.escalation.re_escalation_decision_engine import ReEscalationDecisionEngine
from src.escalation.sla import evaluate_sla_breach

@pytest.fixture
def re_escalation_engine():
    return ReEscalationDecisionEngine()

@pytest.fixture
def base_policy():
    return EscalationPolicy(
        policy_id="test",
        name="test",
        event_type="test",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        base_severity="error",
        reminder_enabled=False,
        reminder_interval_seconds=3600,
        reminder_max_count=3,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=False,
        escalation_enabled=False,
        re_escalation_enabled=True,
        re_escalation_interval_seconds=3600,
        re_escalation_max_count=3,
        sla_target_seconds=7200,
        sla_breach_severity="critical",
        sla_breach_priority="high"
    )

@pytest.fixture
def active_state():
    now = datetime.now()
    return EscalationState(
        state_id="state_1",
        source_event_id="ev_1",
        source_history_id="hist_1",
        source_event_type="test",
        dedupe_key="test_1",
        seller_account_id="seller_1",
        environment_type="sandbox",
        sku="sku_1",
        current_status="escalated",
        current_severity="error",
        current_priority="high",
        escalation_level=1,
        first_seen_at=now - timedelta(hours=2),
        last_escalated_at=now - timedelta(minutes=90)
    )

def test_re_escalation_interval_met(re_escalation_engine, base_policy, active_state):
    now = datetime.now()
    # last escalated was 90m ago, interval is 60m -> should re_escalate
    decision = re_escalation_engine.evaluate(active_state, base_policy, now)
    assert decision == "re_escalate"

def test_re_escalation_interval_not_met(re_escalation_engine, base_policy, active_state):
    now = datetime.now()
    # update last escalated to 30m ago
    active_state.last_escalated_at = now - timedelta(minutes=30)
    decision = re_escalation_engine.evaluate(active_state, base_policy, now)
    assert decision == "skip_interval_not_met"

def test_re_escalation_maxed_out(re_escalation_engine, base_policy, active_state):
    now = datetime.now()
    active_state.re_escalation_count = 3
    decision = re_escalation_engine.evaluate(active_state, base_policy, now)
    assert decision == "skip_maxed_out"

def test_re_escalation_disabled(re_escalation_engine, base_policy, active_state):
    now = datetime.now()
    base_policy.re_escalation_enabled = False
    decision = re_escalation_engine.evaluate(active_state, base_policy, now)
    assert decision == "skip_not_enabled"

def test_sla_breach_evaluation(base_policy, active_state):
    now = datetime.now()
    
    # Not breached (1 hour old vs 2 hour SLA)
    active_state.first_seen_at = now - timedelta(hours=1)
    is_breached, sev, pri = evaluate_sla_breach(active_state, base_policy, now)
    assert not is_breached
    
    # Breached (3 hours old vs 2 hour SLA)
    active_state.first_seen_at = now - timedelta(hours=3)
    is_breached, sev, pri = evaluate_sla_breach(active_state, base_policy, now)
    assert is_breached
    assert sev == "critical"
    assert pri == "high"

def test_sla_no_target(base_policy, active_state):
    now = datetime.now()
    base_policy.sla_target_seconds = None
    active_state.first_seen_at = now - timedelta(hours=10)
    is_breached, _, _ = evaluate_sla_breach(active_state, base_policy, now)
    assert not is_breached
