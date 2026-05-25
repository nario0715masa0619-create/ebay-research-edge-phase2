from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime
from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.models.history_query import HistoryEventView

class AlertDigestService:
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()
        self.dashboard_service = ExecutionDashboardService(self.repository)

    def generate_alert_digest(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        return {
            "date_range": (date_range[0].isoformat(), date_range[1].isoformat()),
            "alert_count_by_level": self.get_alert_count_by_level(date_range),
            "recent_alerts": [
                event.__dict__ for event in self.get_recent_alerts(date_range, limit=20)
            ],
            "by_seller": self.get_alert_by_seller(date_range),
            "by_environment": self.get_alert_by_environment(date_range)
        }

    def get_alert_count_by_level(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        return self.dashboard_service.get_alert_distribution(date_range)

    def get_recent_alerts(self, date_range: Tuple[datetime, datetime], limit: int = 20) -> List[HistoryEventView]:
        from src.listing_execution.models.history_query import HistoryQuery
        query = HistoryQuery(
            event_type="alert_created",
            date_range=date_range,
            limit=limit
        )
        results = self.repository.paginate(query)
        return [self.dashboard_service.query_service._map_to_view(r) for r in results["items"]]

    def _get_alert_count_by_dimension(self, dimension_col, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        from src.db.session import SessionManager
        from src.listing_execution.models.execution_history import ExecutionHistoryModel
        from src.db.models import ExecutionAttemptModel
        from sqlalchemy import func
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(dimension_col, func.count(ExecutionHistoryModel.id))
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionHistoryModel.event_type == "alert_created")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            q = q.group_by(dimension_col)
            return {r[0] or "unknown": r[1] for r in q.all()}
        finally:
            if not self.repository._session:
                session.close()

    def get_alert_by_seller(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        from src.db.models import ExecutionAttemptModel
        return self._get_alert_count_by_dimension(ExecutionAttemptModel.seller_account_id, date_range)

    def get_alert_by_environment(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        from src.db.models import ExecutionAttemptModel
        return self._get_alert_count_by_dimension(ExecutionAttemptModel.environment, date_range)
