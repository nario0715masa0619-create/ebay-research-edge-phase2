from typing import List
from src.ebay.models import MonitoringEvent

class MonitoringEventRepository:
    def __init__(self):
        self._events = []

    def save(self, event: MonitoringEvent):
        self._events.append(event)

    def list_by_candidate_id(self, candidate_id: str) -> List[MonitoringEvent]:
        return [e for e in self._events if e.candidate_id == candidate_id]

    def list_all(self) -> List[MonitoringEvent]:
        return self._events
