from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional
from sqlalchemy import String, Boolean, Text, JSON, DateTime, ForeignKey, Column, Index
from src.db.base import Base

class ExecutionHistoryModel(Base):
    """
    ExecutionHistory Model for Phase J
    Records an append-only audit trail of execution events.
    """
    __tablename__ = 'execution_history'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(255), ForeignKey('execution_attempts.attempt_id'), nullable=False, index=True)
    listing_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    
    dry_run = Column(Boolean, default=False, nullable=False)
    
    from_state = Column(String(50), nullable=True)
    to_state = Column(String(50), nullable=True)
    
    error_code = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(50), nullable=True, default="system")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "listing_id": self.listing_id,
            "event_type": self.event_type,
            "dry_run": self.dry_run,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionHistoryModel":
        # Remove any fields not in model
        valid_keys = {
            "id", "attempt_id", "listing_id", "event_type", "dry_run",
            "from_state", "to_state", "error_code", "error_message",
            "details", "created_at", "created_by"
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        if "created_at" in filtered and isinstance(filtered["created_at"], str):
            filtered["created_at"] = datetime.fromisoformat(filtered["created_at"].replace('Z', '+00:00'))
        return cls(**filtered)
