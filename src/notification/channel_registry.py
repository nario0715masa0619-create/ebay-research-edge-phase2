from typing import Dict, Any
from .models import NotificationEvent, NotificationDispatchResult

class BaseNotifier:
    def send(self, event: NotificationEvent) -> NotificationDispatchResult:
        raise NotImplementedError()

class NotificationChannelRegistry:
    def __init__(self):
        self.notifiers: Dict[str, BaseNotifier] = {}

    def register(self, name: str, notifier: BaseNotifier):
        self.notifiers[name] = notifier

    def get_notifier(self, name: str) -> BaseNotifier:
        return self.notifiers.get(name)
