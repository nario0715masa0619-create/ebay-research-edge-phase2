import pytest
from src.notification.models import NotificationEvent, NotificationRule
from src.notification.rules import get_default_notification_rules
from src.notification.rule_engine import NotificationRuleEngine

def test_resolve_critical_auth_rule():
    rules = get_default_notification_rules()
    engine = NotificationRuleEngine(rules)
    
    event = NotificationEvent(
        event_type="auth_refresh_failed",
        severity="critical",
        title="Auth Fail"
    )
    
    matched = engine.resolve_rules(event)
    assert len(matched) >= 1
    assert any(r.rule_name == "Auth Critical" for r in matched)
    assert "slack" in matched[0].channel_targets

def test_resolve_job_failure_rule():
    rules = get_default_notification_rules()
    engine = NotificationRuleEngine(rules)
    
    event = NotificationEvent(
        event_type="scheduled_job_failed",
        severity="error",
        title="Job Fail"
    )
    
    matched = engine.resolve_rules(event)
    assert len(matched) >= 1
    assert any(r.rule_name == "Job Failure" for r in matched)

def test_resolve_drift_rule():
    rules = get_default_notification_rules()
    engine = NotificationRuleEngine(rules)
    
    event = NotificationEvent(
        event_type="listing_drift_detected",
        severity="warning",
        title="Drift"
    )
    
    matched = engine.resolve_rules(event)
    assert len(matched) >= 1
    assert any(r.rule_name == "Drift Warning" for r in matched)
