from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.db.session import SessionManager
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.history_query import HistoryQuery

class ExecutionHistoryRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self._session = db_session

    def create(self, history_data: Dict[str, Any]) -> ExecutionHistoryModel:
        """
        Creates a new append-only execution history event.
        """
        if "created_at" in history_data:
            # Enforce immutability / set explicitly or let DB handle
            pass
        else:
            history_data["created_at"] = datetime.now(timezone.utc)
            
        model = ExecutionHistoryModel(**history_data)
        
        session = self._session or SessionManager().get_session()
        try:
            session.add(model)
            session.commit()
            session.refresh(model)
            return model
        finally:
            if not self._session:
                session.close()
                
    def get_by_attempt_id(self, attempt_id: str) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            return session.query(ExecutionHistoryModel).filter(
                ExecutionHistoryModel.attempt_id == attempt_id
            ).order_by(ExecutionHistoryModel.created_at.asc()).all()
        finally:
            if not self._session:
                session.close()

    def get_by_listing_id(self, listing_id: str) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            return session.query(ExecutionHistoryModel).filter(
                ExecutionHistoryModel.listing_id == listing_id
            ).order_by(ExecutionHistoryModel.created_at.asc()).all()
        finally:
            if not self._session:
                session.close()

    def list_by_event_type(self, event_type: str) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            return session.query(ExecutionHistoryModel).filter(
                ExecutionHistoryModel.event_type == event_type
            ).order_by(ExecutionHistoryModel.created_at.desc()).all()
        finally:
            if not self._session:
                session.close()

    def find_by_date_range(self, from_date: datetime, to_date: datetime) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            return session.query(ExecutionHistoryModel).filter(
                ExecutionHistoryModel.created_at >= from_date,
                ExecutionHistoryModel.created_at <= to_date
            ).order_by(ExecutionHistoryModel.created_at.desc()).all()
        finally:
            if not self._session:
                session.close()

    def query_by_filters(self, query: HistoryQuery) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            return self._apply_filters(session, query).all()
        finally:
            if not self._session:
                session.close()

    def paginate(self, query: HistoryQuery) -> Dict[str, Any]:
        session = self._session or SessionManager().get_session()
        try:
            base_query = self._apply_filters(session, query)
            total = base_query.count()
            items = base_query.limit(query.limit).offset(query.offset).all()
            return {
                "total": total,
                "items": items,
                "limit": query.limit,
                "offset": query.offset
            }
        finally:
            if not self._session:
                session.close()

    def get_event_counts(self, query: HistoryQuery) -> Dict[str, int]:
        from sqlalchemy import func
        session = self._session or SessionManager().get_session()
        try:
            base_query = self._apply_filters(session, query)
            subq = base_query.subquery()
            results = session.query(
                subq.c.event_type, func.count(subq.c.id)
            ).select_from(subq).group_by(subq.c.event_type).all()
            return {r[0]: r[1] for r in results}
        finally:
            if not self._session:
                session.close()

    def get_timeline(self, attempt_id: Optional[str] = None, listing_id: Optional[str] = None) -> List[ExecutionHistoryModel]:
        session = self._session or SessionManager().get_session()
        try:
            q = session.query(ExecutionHistoryModel)
            if attempt_id:
                q = q.filter(ExecutionHistoryModel.attempt_id == attempt_id)
            if listing_id:
                q = q.filter(ExecutionHistoryModel.listing_id == listing_id)
            return q.order_by(ExecutionHistoryModel.created_at.asc()).all()
        finally:
            if not self._session:
                session.close()

    def _apply_filters(self, session: Session, query: HistoryQuery):
        q = session.query(ExecutionHistoryModel)
        
        # Need to join ExecutionAttemptModel if we filter by seller_account_id, environment, or status
        needs_join = any([query.seller_account_id, query.environment, query.status])
        if needs_join:
            q = q.join(ExecutionAttemptModel, ExecutionHistoryModel.attempt_id == ExecutionAttemptModel.attempt_id)
            
        if query.attempt_id:
            q = q.filter(ExecutionHistoryModel.attempt_id == query.attempt_id)
        if query.listing_id:
            q = q.filter(ExecutionHistoryModel.listing_id == query.listing_id)
        if query.event_type:
            q = q.filter(ExecutionHistoryModel.event_type == query.event_type)
        if query.dry_run is not None:
            q = q.filter(ExecutionHistoryModel.dry_run == query.dry_run)
            
        if query.seller_account_id:
            q = q.filter(ExecutionAttemptModel.seller_account_id == query.seller_account_id)
        if query.environment:
            q = q.filter(ExecutionAttemptModel.environment == query.environment)
        if query.status:
            q = q.filter(ExecutionAttemptModel.status == query.status)
            
        if query.date_range:
            q = q.filter(ExecutionHistoryModel.created_at >= query.date_range[0])
            q = q.filter(ExecutionHistoryModel.created_at <= query.date_range[1])
            
        return q.order_by(ExecutionHistoryModel.created_at.desc())
