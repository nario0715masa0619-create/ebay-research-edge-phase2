from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime
from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.models.history_query import HistoryEventView

class FailureDigestService:
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()
        self.dashboard_service = ExecutionDashboardService(self.repository)

    def generate_failure_digest(self, date_range: Tuple[datetime, datetime], limit: int = 50) -> Dict[str, Any]:
        return {
            "date_range": (date_range[0].isoformat(), date_range[1].isoformat()),
            "top_error_codes": self.get_top_error_codes(date_range, limit=10),
            "top_failure_boundaries": self.get_top_failure_boundaries(date_range, limit=10),
            "recent_failures": [
                event.__dict__ for event in self.get_recent_failures(date_range, limit=limit)
            ],
            "by_seller": self.get_failure_by_seller(date_range),
            "by_environment": self.get_failure_by_environment(date_range)
        }

    def get_top_error_codes(self, date_range: Tuple[datetime, datetime], limit: int = 10) -> List[Tuple[str, int]]:
        return self.dashboard_service.get_top_error_codes(limit=limit, date_range=date_range)

    def get_top_failure_boundaries(self, date_range: Tuple[datetime, datetime], limit: int = 10) -> List[Tuple[str, int]]:
        return self.dashboard_service.get_top_failure_boundaries(limit=limit, date_range=date_range)

    def get_recent_failures(self, date_range: Tuple[datetime, datetime], limit: int = 20) -> List[HistoryEventView]:
        from src.listing_execution.models.history_query import HistoryQuery
        # HistoryQuery can accept date_range and event_type
        query = HistoryQuery(
            event_type="execution_failed",
            date_range=date_range,
            limit=limit
        )
        results = self.repository.paginate(query)
        return [self.dashboard_service.query_service._map_to_view(r) for r in results["items"]]

    def get_failure_by_seller(self, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        return self.dashboard_service.get_seller_failure_analysis(date_range)

    def get_failure_by_environment(self, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        return self.dashboard_service.get_environment_failure_analysis(date_range)
