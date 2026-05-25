from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.models.history_query import HistoryQuery, HistoryEventView
from src.listing_execution.models.execution_history import ExecutionHistoryModel

class ExecutionHistoryQueryService:
    """
    Read-only service for querying and filtering execution history events.
    Respects append-only nature of the history layer.
    """
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()

    def _map_to_view(self, model: ExecutionHistoryModel) -> HistoryEventView:
        return HistoryEventView(
            event_id=model.id,
            attempt_id=model.attempt_id,
            listing_id=model.listing_id,
            event_type=model.event_type,
            dry_run=model.dry_run,
            from_state=model.from_state,
            to_state=model.to_state,
            error_code=model.error_code,
            error_message=model.error_message,
            details=model.details,
            created_at=model.created_at,
            created_by=model.created_by
        )

    def find_by_attempt_id(self, attempt_id: str) -> List[HistoryEventView]:
        query = HistoryQuery(attempt_id=attempt_id)
        results = self.repository.query_by_filters(query)
        return [self._map_to_view(r) for r in results]

    def find_by_listing_id(self, listing_id: str) -> List[HistoryEventView]:
        query = HistoryQuery(listing_id=listing_id)
        results = self.repository.query_by_filters(query)
        return [self._map_to_view(r) for r in results]

    def find_by_seller_account_id(self, seller_account_id: str) -> List[HistoryEventView]:
        query = HistoryQuery(seller_account_id=seller_account_id)
        results = self.repository.query_by_filters(query)
        return [self._map_to_view(r) for r in results]

    def find_by_event_type(self, event_type: str) -> List[HistoryEventView]:
        query = HistoryQuery(event_type=event_type)
        results = self.repository.query_by_filters(query)
        return [self._map_to_view(r) for r in results]

    def find_by_date_range(self, from_date: datetime, to_date: datetime) -> List[HistoryEventView]:
        query = HistoryQuery(date_range=(from_date, to_date))
        results = self.repository.query_by_filters(query)
        return [self._map_to_view(r) for r in results]

    def find_recent(self, limit: int = 50) -> List[HistoryEventView]:
        query = HistoryQuery(limit=limit)
        results = self.repository.paginate(query)
        return [self._map_to_view(r) for r in results["items"]]

    def find_failed_recent(self, limit: int = 50) -> List[HistoryEventView]:
        now = datetime.now(timezone.utc)
        query = HistoryQuery(
            event_type="execution_failed", 
            date_range=(now - timedelta(days=7), now),
            limit=limit
        )
        results = self.repository.paginate(query)
        return [self._map_to_view(r) for r in results["items"]]

    def apply_filters(self, query: HistoryQuery) -> Dict[str, Any]:
        result = self.repository.paginate(query)
        return {
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "items": [self._map_to_view(r) for r in result["items"]]
        }
