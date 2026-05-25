from typing import Tuple, Optional, List
from datetime import datetime
from sqlalchemy import func
from src.db.session import SessionManager
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.health_report import SellerHealthReport

class SellerHealthAnalysisService:
    def __init__(self, repository: Optional[ExecutionHistoryRepository] = None):
        self.repository = repository or ExecutionHistoryRepository()

    def analyze_seller_health(self, seller_id: str, date_range: Tuple[datetime, datetime]) -> SellerHealthReport:
        volume = self.get_seller_execution_volume(seller_id, date_range)
        failure_rate = self.get_seller_failure_rate(seller_id, date_range)
        guards = self.get_seller_guard_rejection_count(seller_id, date_range)
        retries = self.get_seller_retry_rollback_count(seller_id, date_range)
        patterns = self.get_seller_major_error_patterns(seller_id, date_range, limit=5)
        
        return SellerHealthReport(
            seller_id=seller_id,
            date_range=(date_range[0].isoformat(), date_range[1].isoformat()),
            execution_volume=volume,
            failure_rate=failure_rate,
            guard_rejection_count=guards,
            retry_rollback_count=retries,
            major_error_patterns=patterns
        )

    def get_seller_execution_volume(self, seller_id: str, date_range: Tuple[datetime, datetime]) -> int:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(func.count(ExecutionAttemptModel.attempt_id))
            q = q.filter(ExecutionAttemptModel.seller_account_id == seller_id)
            q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            return q.scalar() or 0
        finally:
            if not self.repository._session:
                session.close()

    def get_seller_failure_rate(self, seller_id: str, date_range: Tuple[datetime, datetime]) -> float:
        from sqlalchemy import case
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(
                func.sum(case((ExecutionAttemptModel.status == 'failed', 1), else_=0)),
                func.count(ExecutionAttemptModel.attempt_id)
            )
            q = q.filter(ExecutionAttemptModel.seller_account_id == seller_id)
            q = q.filter(ExecutionAttemptModel.created_at >= date_range[0], ExecutionAttemptModel.created_at <= date_range[1])
            failed, total = q.first() or (0, 0)
            failed = failed or 0
            total = total or 0
            return (failed / total) if total > 0 else 0.0
        finally:
            if not self.repository._session:
                session.close()

    def get_seller_guard_rejection_count(self, seller_id: str, date_range: Tuple[datetime, datetime]) -> int:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(func.count(ExecutionHistoryModel.id))
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.seller_account_id == seller_id)
            q = q.filter(ExecutionHistoryModel.event_type == "guard_rejected")
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            return q.scalar() or 0
        finally:
            if not self.repository._session:
                session.close()

    def get_seller_retry_rollback_count(self, seller_id: str, date_range: Tuple[datetime, datetime]) -> int:
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(func.count(ExecutionHistoryModel.id))
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.seller_account_id == seller_id)
            q = q.filter(ExecutionHistoryModel.event_type.in_(["retry_scheduled", "rollback_executed"]))
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            return q.scalar() or 0
        finally:
            if not self.repository._session:
                session.close()

    def get_seller_major_error_patterns(self, seller_id: str, date_range: Tuple[datetime, datetime], limit: int = 5) -> List[Tuple[str, int]]:
        from sqlalchemy import desc
        session = self.repository._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel.error_code, func.count(ExecutionHistoryModel.id))
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            q = q.filter(ExecutionAttemptModel.seller_account_id == seller_id)
            q = q.filter(ExecutionHistoryModel.event_type == "execution_failed")
            q = q.filter(ExecutionHistoryModel.error_code.isnot(None))
            q = q.filter(ExecutionHistoryModel.created_at >= date_range[0], ExecutionHistoryModel.created_at <= date_range[1])
            q = q.group_by(ExecutionHistoryModel.error_code).order_by(desc(func.count(ExecutionHistoryModel.id))).limit(limit)
            return [(r[0], r[1]) for r in q.all()]
        finally:
            if not self.repository._session:
                session.close()
