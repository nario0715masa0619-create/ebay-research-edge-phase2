from typing import Dict
from datetime import datetime, timedelta
from .models import NotificationEvent

class NotificationDeduper:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.last_seen: Dict[str, datetime] = {} # {dedupe_key: timestamp}

    def should_dedupe(self, event: NotificationEvent, window_override: int = None) -> bool:
        key = event.dedupe_key or self._generate_key(event)
        if not key:
            return False
            
        now = datetime.now()
        window = window_override if window_override is not None else self.window_seconds
        
        if key in self.last_seen:
            elapsed = (now - self.last_seen[key]).total_seconds()
            if elapsed < window:
                return True
        
        self.last_seen[key] = now
        return False

    def _generate_key(self, event: NotificationEvent) -> str:
        # Default key generation: type + layer + (sku if present)
        key = f"{event.event_type}:{event.source_layer}"
        if event.sku:
            key += f":{event.sku}"
        elif event.source_run_id:
            key += f":{event.source_run_id}"
        return key
