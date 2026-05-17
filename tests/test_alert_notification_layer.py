import pytest
from unittest.mock import MagicMock
from src.notification.models import NotificationEvent, NotificationRule
from src.notification.rule_engine import NotificationRuleEngine
from src.notification.dispatcher import NotificationDispatcher
from src.notification.deduper import NotificationDeduper
from src.notification.cooldown import NotificationCooldownManager
from src.notification.channel_registry import NotificationChannelRegistry, BaseNotifier
from src.notification.severity_classifier import NotificationSeverityClassifier

@pytest.fixture
def mock_notifier():
    notifier = MagicMock(spec=BaseNotifier)
    notifier.send.return_value = MagicMock(success_flag=True)
    return notifier

@pytest.fixture
def dispatcher(mock_notifier):
    rule = NotificationRule(
        rule_name="Test Rule",
        event_types=["test_event"],
        channel_targets=["test_channel"],
        dedupe_window_seconds=10
    )
    rule_engine = NotificationRuleEngine([rule])
    deduper = NotificationDeduper(window_seconds=10)
    cooldown_manager = NotificationCooldownManager(default_cooldown_seconds=10)
    registry = NotificationChannelRegistry()
    registry.register("test_channel", mock_notifier)
    
    dispatcher = NotificationDispatcher(rule_engine, deduper, cooldown_manager, registry)
    dispatcher.classifier = NotificationSeverityClassifier()
    return dispatcher

def test_notify_success(dispatcher, mock_notifier):
    event = NotificationEvent(
        event_type="test_event",
        title="Test Notification"
    )
    
    res = dispatcher.notify(event)
    
    assert res.processed_count == 1
    assert res.dispatched_count == 1
    mock_notifier.send.assert_called_once()
    assert event.severity == "info" # Classified automatically

def test_dedupe(dispatcher, mock_notifier):
    event = NotificationEvent(
        event_type="test_event",
        title="Test Notification",
        sku="SKU-1"
    )
    
    # First call
    dispatcher.notify(event)
    assert mock_notifier.send.call_count == 1
    
    # Second call (immediate)
    res = dispatcher.notify(event)
    assert res.deduped_count == 1
    assert mock_notifier.send.call_count == 1 # Still 1

def test_severity_classification(dispatcher):
    event = NotificationEvent(
        event_type="auth_refresh_failed",
        title="Auth Fail"
    )
    
    dispatcher.notify(event)
    assert event.severity == "critical"
    assert event.priority == "urgent"

def test_dry_run(dispatcher, mock_notifier):
    event = NotificationEvent(
        event_type="test_event",
        title="Test"
    )
    
    res = dispatcher.notify(event, dry_run=True)
    assert res.skipped_count == 1
    assert mock_notifier.send.call_count == 0
