from typing import List, Dict, Any, Optional
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.services.execution_history_query_service import ExecutionHistoryQueryService
from src.listing_execution.models.history_query import HistoryEventView

class ExecutionAuditTimelineService:
    """
    Constructs comprehensive timelines for execution attempts and listings.
    Supports filtering and extraction of key lifecycle events.
    """
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()
        self.query_service = ExecutionHistoryQueryService(self.repository)

    def build_attempt_timeline(self, attempt_id: str) -> List[HistoryEventView]:
        """
        Builds a chronological timeline of events for a specific execution attempt.
        """
        # Since repository.get_timeline is ordered asc, we just map it
        models = self.repository.get_timeline(attempt_id=attempt_id)
        return [self.query_service._map_to_view(m) for m in models]

    def build_listing_timeline(self, listing_id: str) -> List[HistoryEventView]:
        """
        Builds a chronological timeline of all execution attempts across a single listing.
        """
        models = self.repository.get_timeline(listing_id=listing_id)
        return [self.query_service._map_to_view(m) for m in models]

    def extract_state_transitions(self, events: List[HistoryEventView]) -> List[HistoryEventView]:
        """
        Filters a timeline to only include explicit state transitions.
        """
        state_events = {"execution_started", "execution_succeeded", "execution_failed", "rollback_executed"}
        return [e for e in events if e.event_type in state_events]

    def filter_critical_events(self, events: List[HistoryEventView]) -> List[HistoryEventView]:
        """
        Filters a timeline to highlight critical events such as errors, guards, and alerts.
        """
        critical_events = {
            "execution_failed", "alert_created", "guard_rejected", 
            "readiness_failed", "rollback_executed"
        }
        return [e for e in events if e.event_type in critical_events]
