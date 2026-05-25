from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.db.session import SessionManager
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.dashboard_summary import DashboardSummary, DashboardCard
from src.listing_execution.models.history_query import HistoryQuery, HistoryEventView
from src.listing_execution.services.execution_history_query_service import ExecutionHistoryQueryService
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository

class ExecutionDashboardService:
    """
    Service for calculating execution layer analytics, dashboard summaries, 
    and performance metrics. Prioritizes read-only aggregation.
    """
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()
        self.query_service = ExecutionHistoryQueryService(self.repository)

    def get_overview_summary(self, date_range: Tuple[datetime, datetime]) -> DashboardSummary:
        counts = self.get_execution_counts(date_range)
        succeeded = counts.get("execution_succeeded", 0)
        failed = counts.get("execution_failed", 0)
        rolled_back = counts.get("rollback_executed", 0)
        alert_count = counts.get("alert_created", 0)
        guard_rejection_count = counts.get("guard_rejected", 0)
        
        total_exec_started = counts.get("execution_started", 0)
        success_rate = (succeeded / total_exec_started) if total_exec_started > 0 else 0.0
        failure_rate = (failed / total_exec_started) if total_exec_started > 0 else 0.0

        alert_dist = self.get_alert_distribution(date_range)
        top_errors = self.get_top_error_codes(limit=5, date_range=date_range)
        top_boundaries = self.get_top_failure_boundaries(limit=5, date_range=date_range)
        dry_vs_live = self.get_dry_run_vs_live_split(date_range)
        seller_rates = self.get_seller_failure_analysis(date_range)
        env_rates = self.get_environment_failure_analysis(date_range)

        return DashboardSummary(
            total_executions=total_exec_started,
            succeeded=succeeded,
            failed=failed,
            rolled_back=rolled_back,
            alert_count=alert_count,
            success_rate=success_rate,
            failure_rate=failure_rate,
            alert_level_distribution=alert_dist,
            top_error_codes=top_errors,
            top_failure_boundaries=top_boundaries,
            dry_run_count=dry_vs_live.get("dry_run", 0),
            live_count=dry_vs_live.get("live", 0),
            seller_failure_rates=seller_rates,
            environment_failure_rates=env_rates,
            guard_rejection_count=guard_rejection_count,
            created_at=datetime.now(timezone.utc)
        )

    def get_execution_counts(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        query = HistoryQuery(date_range=date_range)
        return self.repository.get_event_counts(query)

    def get_success_failure_ratio(self, date_range: Tuple[datetime, datetime]) -> Tuple[int, int, float]:
        counts = self.get_execution_counts(date_range)
        succeeded = counts.get("execution_succeeded", 0)
        failed = counts.get("execution_failed", 0)
        total = succeeded + failed
        rate = (succeeded / total) if total > 0 else 0.0
        return succeeded, failed, rate

    def get_top_error_codes(self, limit: int = 5, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Tuple[str, int]]:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel.error_code, func.count(ExecutionHistoryModel.id))
            q = q.filter(ExecutionHistoryModel.event_type == "execution_failed")
            q = q.filter(ExecutionHistoryModel.error_code.isnot(None))
            if date_range:
                q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            q = q.group_by(ExecutionHistoryModel.error_code).order_by(desc(func.count(ExecutionHistoryModel.id))).limit(limit)
            return [(r[0], r[1]) for r in q.all()]
        finally:
            if not self.repository._session:
                session.close()

    def get_top_failure_boundaries(self, limit: int = 5, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Tuple[str, int]]:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionAttemptModel.failure_boundary, func.count(ExecutionAttemptModel.attempt_id))
            q = q.filter(ExecutionAttemptModel.status == "failed")
            q = q.filter(ExecutionAttemptModel.failure_boundary.isnot(None))
            if date_range:
                q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            q = q.group_by(ExecutionAttemptModel.failure_boundary).order_by(desc(func.count(ExecutionAttemptModel.attempt_id))).limit(limit)
            return [(r[0], r[1]) for r in q.all()]
        finally:
            if not self.repository._session:
                session.close()

    def get_alert_distribution(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        session = self.repository._session or SessionManager().get_session()
        try:
            # Alerts details hold 'alert_level'
            # We can parse JSON in app memory if DB doesn't support JSON agg easily,
            # but since sqlite JSON1 might not be uniformly available, we'll fetch them.
            q = session.query(ExecutionHistoryModel.details)
            q = q.filter(ExecutionHistoryModel.event_type == "alert_created")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            dist = {}
            for row in q.all():
                details = row[0] or {}
                level = details.get("alert_level", "UNKNOWN")
                dist[level] = dist.get(level, 0) + 1
            return dist
        finally:
            if not self.repository._session:
                session.close()

    def get_dry_run_vs_live_split(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel.dry_run, func.count(ExecutionHistoryModel.id))
            q = q.filter(ExecutionHistoryModel.event_type == "execution_started")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            q = q.group_by(ExecutionHistoryModel.dry_run)
            res = {}
            for r in q.all():
                key = "dry_run" if r[0] else "live"
                res[key] = r[1]
            return res
        finally:
            if not self.repository._session:
                session.close()

    def _get_failure_rate_by_dimension(self, dimension_col, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        from sqlalchemy import case
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(
                dimension_col,
                func.sum(case((ExecutionAttemptModel.status == 'failed', 1), else_=0)),
                func.count(ExecutionAttemptModel.attempt_id)
            )
            q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            q = q.group_by(dimension_col)
            rates = {}
            for dim, failed, total in q.all():
                if dim is not None:
                    rates[dim] = (failed / total) if total > 0 else 0.0
            return rates
        finally:
            if not self.repository._session:
                session.close()

    def get_seller_failure_analysis(self, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        return self._get_failure_rate_by_dimension(ExecutionAttemptModel.seller_account_id, date_range)

    def get_environment_failure_analysis(self, date_range: Tuple[datetime, datetime]) -> Dict[str, float]:
        return self._get_failure_rate_by_dimension(ExecutionAttemptModel.environment, date_range)

    def get_recent_failures(self, limit: int = 20) -> List[HistoryEventView]:
        return self.query_service.find_failed_recent(limit=limit)

    def get_recent_alerts(self, limit: int = 20) -> List[Any]:
        # 'alert_created' events
        query = HistoryQuery(event_type="alert_created", limit=limit)
        results = self.repository.paginate(query)
        return [self.query_service._map_to_view(r) for r in results["items"]]

    def get_state_transition_summary(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        counts = self.get_execution_counts(date_range)
        return {
            "started": counts.get("execution_started", 0),
            "succeeded": counts.get("execution_succeeded", 0),
            "failed": counts.get("execution_failed", 0),
            "rolled_back": counts.get("rollback_executed", 0)
        }

    def get_guard_rejection_summary(self, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel.error_message, func.count(ExecutionHistoryModel.id))
            q = q.filter(ExecutionHistoryModel.event_type == "guard_rejected")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            q = q.group_by(ExecutionHistoryModel.error_message)
            return {r[0] or "unknown": r[1] for r in q.all()}
        finally:
            if not self.repository._session:
                session.close()
