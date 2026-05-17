from typing import List, Dict, Any, Optional
from src.notification.rule_engine import NotificationRuleEngine
from src.notification.models import NotificationEvent

class NotificationRuleInspectService:
    def __init__(self, rule_engine: NotificationRuleEngine):
        self.rule_engine = rule_engine

    def list_rules(self) -> List[Dict[str, Any]]:
        return [self._to_view(r) for r in self.rule_engine.rules]

    def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        for r in self.rule_engine.rules:
            if r.rule_name == rule_name:
                return self._to_view(r)
        return None

    def find_rules_for_event(self, event_type: str, severity: str = "info") -> List[Dict[str, Any]]:
        # Simulate an event
        event = NotificationEvent(event_type=event_type, title="Simulation", severity=severity)
        matched = self.rule_engine.resolve_rules(event)
        return [self._to_view(r) for r in matched]

    def _to_view(self, rule) -> Dict[str, Any]:
        return {
            "rule_name": rule.rule_name,
            "enabled": rule.enabled,
            "event_types": rule.event_types or ["all"],
            "severities": rule.severities or ["all"],
            "priorities": rule.priorities or ["all"],
            "channels": rule.channel_targets,
            "cooldown": rule.cooldown_seconds,
            "dedupe_window": rule.dedupe_window_seconds,
            "template": rule.template_name or "default"
        }
