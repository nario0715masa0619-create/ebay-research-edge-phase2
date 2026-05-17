import os
from .models import NotificationRule
from .rules import get_default_notification_rules
from .rule_engine import NotificationRuleEngine
from .deduper import NotificationDeduper
from .cooldown import NotificationCooldownManager
from .channel_registry import NotificationChannelRegistry
from .dispatcher import NotificationDispatcher
from .severity_classifier import NotificationSeverityClassifier
from .notifiers.console_notifier import ConsoleNotifier
from .notifiers.slack_notifier import SlackNotifier

class NotificationBootstrap:
    @staticmethod
    def bootstrap(history_repo=None, seller_resolver=None) -> NotificationDispatcher:
        # 1. Define default rules
        rules = get_default_notification_rules()
        
        # 2. Setup components
        rule_engine = NotificationRuleEngine(rules)
        deduper = NotificationDeduper()
        cooldown_manager = NotificationCooldownManager()
        classifier = NotificationSeverityClassifier()
        
        registry = NotificationChannelRegistry()
        registry.register("console", ConsoleNotifier())
        
        slack_webhook = os.environ.get("NOTIFICATION_SLACK_WEBHOOK_URL")
        if slack_webhook:
            registry.register("slack", SlackNotifier(slack_webhook))
            
        dispatcher = NotificationDispatcher(rule_engine, deduper, cooldown_manager, registry, seller_resolver=seller_resolver)
        dispatcher.history_repo = history_repo
        dispatcher.classifier = classifier
        
        return dispatcher
