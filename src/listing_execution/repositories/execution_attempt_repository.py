import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.db.models import ExecutionAttemptModel

class ExecutionAttemptRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_attempt(self, attempt_data: Dict[str, Any]) -> ExecutionAttemptModel:
        """
        Creates a new execution attempt record.
        """
        # Ensure payload_json is stringified if dict is provided
        payload = attempt_data.get('payload_json')
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            
        model = ExecutionAttemptModel(
            attempt_id=attempt_data['attempt_id'],
            listing_id=attempt_data['listing_id'],
            candidate_id=attempt_data.get('candidate_id'),
            handoff_id=attempt_data.get('handoff_id'),
            seller_account_id=attempt_data['seller_account_id'],
            environment=attempt_data['environment'],
            status=attempt_data.get('status', 'pending'),
            payload_json=payload,
            result_summary=attempt_data.get('result_summary'),
            error_code=attempt_data.get('error_code'),
            error_message=attempt_data.get('error_message'),
            failure_boundary=attempt_data.get('failure_boundary'),
            retry_count=attempt_data.get('retry_count', 0),
            executed_at=attempt_data.get('executed_at'),
            finished_at=attempt_data.get('finished_at'),
            ranking_decision_id=attempt_data.get('ranking_decision_id'),
            scheduler_run_id=attempt_data.get('scheduler_run_id'),
            batch_id=attempt_data.get('batch_id')
        )
        self.session.add(model)
        self.session.commit()
        return model

    def get_by_id(self, attempt_id: str) -> Optional[ExecutionAttemptModel]:
        """
        Retrieve attempt by attempt_id
        """
        return self.session.query(ExecutionAttemptModel).filter(
            ExecutionAttemptModel.attempt_id == attempt_id
        ).first()

    def get_by_listing_id(self, listing_id: str) -> List[ExecutionAttemptModel]:
        """
        Retrieve all attempts for a given listing_id
        """
        return self.session.query(ExecutionAttemptModel).filter(
            ExecutionAttemptModel.listing_id == listing_id
        ).order_by(ExecutionAttemptModel.created_at.asc()).all()

    def update_status(
        self, 
        attempt_id: str, 
        status: str, 
        error_code: Optional[str] = None, 
        error_message: Optional[str] = None,
        failure_boundary: Optional[str] = None,
        finished_at: Optional[datetime] = None
    ) -> Optional[ExecutionAttemptModel]:
        """
        Update the status and optional error details for an attempt.
        """
        model = self.get_by_id(attempt_id)
        if not model:
            return None
            
        model.status = status
        
        if error_code is not None:
            model.error_code = error_code
        if error_message is not None:
            model.error_message = error_message
        if failure_boundary is not None:
            model.failure_boundary = failure_boundary
        if finished_at is not None:
            model.finished_at = finished_at
            
        self.session.commit()
        return model
