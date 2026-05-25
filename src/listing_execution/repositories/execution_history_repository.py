from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.db.session import SessionManager
from src.listing_execution.models.execution_history import ExecutionHistoryModel

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
