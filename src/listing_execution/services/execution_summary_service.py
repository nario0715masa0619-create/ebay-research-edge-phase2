from typing import Tuple, Optional, Dict, Any
from datetime import datetime, date, timedelta, time, timezone
from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository

class ExecutionSummaryService:
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()
        self.dashboard_service = ExecutionDashboardService(self.repository)

    def _build_summary(self, seller: Optional[str], environment: Optional[str], date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        stats = self.get_execution_stats(date_range)
        succeeded, failed, rate = self.get_success_failure_ratio(date_range)
        alert_count = self.get_alert_count(date_range)
        
        # NOTE: Ideally we filter stats by seller/environment, but dashboard_service.get_execution_counts
        # internally uses HistoryQuery with just date_range. For Phase L Wave 1, we provide a generic
        # skeleton that can be expanded with specific queries.
        # Since we use `ExecutionDashboardService`, its get_execution_counts currently accepts only date_range.
        # To support filter by seller/environment strictly, we would write custom queries here.
        # For now we'll implement custom queries to respect the filters.
        
        from src.db.session import SessionManager
        from src.listing_execution.models.execution_history import ExecutionHistoryModel
        from sqlalchemy import func
        session = self.repository._session or SessionManager().get_session()
        
        counts = {}
        try:
            q = session.query(ExecutionHistoryModel.event_type, func.count(ExecutionHistoryModel.id))
            if seller or environment:
                from src.db.models import ExecutionAttemptModel
                q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            if seller:
                q = q.filter(ExecutionAttemptModel.seller_account_id == seller)
            if environment:
                q = q.filter(ExecutionAttemptModel.environment == environment)
            q = q.group_by(ExecutionHistoryModel.event_type)
            counts = {r[0]: r[1] for r in q.all()}
        finally:
            if not self.repository._session:
                session.close()

        s = counts.get("execution_succeeded", 0)
        f = counts.get("execution_failed", 0)
        t = s + f
        r = (s / t) if t > 0 else 0.0
        a = counts.get("alert_created", 0)

        return {
            "seller": seller,
            "environment": environment,
            "date_range": (date_range[0].isoformat(), date_range[1].isoformat()),
            "total_executed": counts.get("execution_started", 0),
            "succeeded": s,
            "failed": f,
            "success_rate": r,
            "alert_count": a,
            "dry_run_count": counts.get("dry_run_executed", 0) # Just a placeholder count, dry_run vs live is a bit different
        }

    def generate_daily_summary(self, seller: Optional[str], environment: Optional[str], target_date: date) -> Dict[str, Any]:
        start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
        return self._build_summary(seller, environment, (start, end))

    def generate_weekly_summary(self, seller: Optional[str], environment: Optional[str], start_of_week: date) -> Dict[str, Any]:
        start = datetime.combine(start_of_week, time.min, tzinfo=timezone.utc)
        end = datetime.combine(start_of_week + timedelta(days=6), time.max, tzinfo=timezone.utc)
        return self._build_summary(seller, environment, (start, end))

    def generate_monthly_summary(self, seller: Optional[str], environment: Optional[str], year: int, month: int) -> Dict[str, Any]:
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return self._build_summary(seller, environment, (start, end))

    def get_execution_stats(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        return self.dashboard_service.get_execution_counts(date_range)

    def get_success_failure_ratio(self, date_range: Tuple[datetime, datetime]) -> Tuple[int, int, float]:
        return self.dashboard_service.get_success_failure_ratio(date_range)

    def get_alert_count(self, date_range: Tuple[datetime, datetime]) -> int:
        counts = self.dashboard_service.get_execution_counts(date_range)
        return counts.get("alert_created", 0)
