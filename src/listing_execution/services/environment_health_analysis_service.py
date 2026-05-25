from typing import Tuple, Optional, Dict
from datetime import datetime
from sqlalchemy import func
from src.db.session import SessionManager
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.health_report import EnvironmentHealthReport

class EnvironmentHealthAnalysisService:
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()

    def analyze_environment_health(self, environment: str, date_range: Tuple[datetime, datetime]) -> EnvironmentHealthReport:
        volume = self.get_environment_execution_volume(environment, date_range)
        failure_rate = self.get_environment_failure_rate(environment, date_range)
        guards = self.get_environment_guard_rejection_count(environment, date_range)
        alerts = self.get_environment_alert_concentration(environment, date_range)
        dry_run_ratio = self.get_environment_dry_run_ratio(environment, date_range)
        
        return EnvironmentHealthReport(
            environment=environment,
            date_range=(date_range[0].isoformat(), date_range[1].isoformat()),
            execution_volume=volume,
            failure_rate=failure_rate,
            guard_rejection_count=guards,
            alert_concentration=alerts,
            dry_run_ratio=dry_run_ratio
        )

    def get_environment_execution_volume(self, environment: str, date_range: Tuple[datetime, datetime]) -> int:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(func.count(ExecutionAttemptModel.attempt_id))
            q = q.filter(ExecutionAttemptModel.environment == environment)
            q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            return q.scalar() or 0
        finally:
            if not self.repository._session:
                session.close()

    def get_environment_failure_rate(self, environment: str, date_range: Tuple[datetime, datetime]) -> float:
        from sqlalchemy import case
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(
                func.sum(case((ExecutionAttemptModel.status == 'failed', 1), else_=0)),
                func.count(ExecutionAttemptModel.attempt_id)
            )
            q = q.filter(ExecutionAttemptModel.environment == environment)
            q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            failed, total = q.first() or (0, 0)
            failed = failed or 0
            total = total or 0
            return (failed / total) if total > 0 else 0.0
        finally:
            if not self.repository._session:
                session.close()

    def get_environment_guard_rejection_count(self, environment: str, date_range: Tuple[datetime, datetime]) -> int:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(func.count(ExecutionHistoryModel.id))
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.environment == environment)
            q = q.filter(ExecutionHistoryModel.event_type == "guard_rejected")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            return q.scalar() or 0
        finally:
            if not self.repository._session:
                session.close()

    def get_environment_alert_concentration(self, environment: str, date_range: Tuple[datetime, datetime]) -> Dict[str, int]:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel.details)
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.environment == environment)
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

    def get_environment_dry_run_ratio(self, environment: str, date_range: Tuple[datetime, datetime]) -> float:
        session = self.repository._session or SessionManager().get_session()
        try:
            from sqlalchemy import case
            q = session.query(
                func.sum(case((ExecutionHistoryModel.dry_run == True, 1), else_=0)),
                func.count(ExecutionHistoryModel.id)
            )
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.environment == environment)
            q = q.filter(ExecutionHistoryModel.event_type == "execution_started")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            dry_count, total = q.first() or (0, 0)
            dry_count = dry_count or 0
            total = total or 0
            return (dry_count / total) if total > 0 else 0.0
        finally:
            if not self.repository._session:
                session.close()
