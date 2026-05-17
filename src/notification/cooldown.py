from typing import Dict
from datetime import datetime, timedelta
from .models import NotificationEvent

class NotificationCooldownManager:
    def __init__(self, default_cooldown_seconds: int = 300):
        self.default_cooldown_seconds = default_cooldown_seconds
        self.last_dispatched: Dict[str, datetime] = {} # {cooldown_key: timestamp}

    def is_cooling_down(self, event: NotificationEvent, cooldown_override: int = None) -> bool:
        key = self._generate_key(event)
        if not key:
            return False
            
        now = datetime.now()
        cooldown = cooldown_override if cooldown_override is not None else self.default_cooldown_seconds
        
        if key in self.last_dispatched:
            elapsed = (now - self.last_dispatched[key]).total_seconds()
            if elapsed < cooldown:
                return True
        
        return False

    def mark_dispatched(self, event: NotificationEvent):
        key = self._generate_key(event)
        if key:
            self.last_dispatched[key] = datetime.now()

    def _generate_key(self, event: NotificationEvent) -> str:
        # For cooldown, we often want to block the same type of error globally or per SKU
        key = f"cooldown:{event.event_type}"
        if event.sku:
            key += f":{event.sku}"
        return key
