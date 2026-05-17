from typing import List
from .models import NotificationEvent, NotificationRule

class NotificationRuleEngine:
    def __init__(self, rules: List[NotificationRule]):
        self.rules = rules

    def resolve_rules(self, event: NotificationEvent) -> List[NotificationRule]:
        matched = []
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if rule.event_types and event.event_type not in rule.event_types:
                continue
                
            if rule.severities and event.severity not in rule.severities:
                continue
                
            if rule.priorities and event.priority not in rule.priorities:
                continue
                
            matched.append(rule)
            
        return matched
