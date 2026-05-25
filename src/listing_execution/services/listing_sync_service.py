import logging
from typing import Dict, Any
from src.listing_sync.models.listing_state import ListingState
from src.listing_execution.gateways.execution_gateway import ExecutionResult

logger = logging.getLogger(__name__)

class StateConflictError(Exception):
    """Raised when there is a state conflict during sync."""
    pass

class ListingSyncService:
    def __init__(self, repository=None):
        """
        repository: A mock or actual repository that manages listing states and audit logs.
        For Wave 2, we simulate this with an in-memory dictionary if None.
        """
        self.repository = repository
        self._mock_db: Dict[str, ListingState] = {}
        self._audit_logs = []

    def _get_current_state(self, listing_id: str) -> ListingState:
        if self.repository:
            return self.repository.get_state(listing_id)
        return self._mock_db.get(listing_id, ListingState.pending)

    def _update_state(self, listing_id: str, new_state: ListingState):
        if self.repository:
            self.repository.update_state(listing_id, new_state)
        else:
            self._mock_db[listing_id] = new_state

    def _log_audit(self, listing_id: str, attempt_id: str, from_state: ListingState, to_state: ListingState, reason: str, is_dry_run: bool = False):
        log_entry = {
            "listing_id": listing_id,
            "attempt_id": attempt_id,
            "from_state": from_state.value,
            "to_state": to_state.value,
            "reason": reason,
            "is_dry_run": is_dry_run
        }
        if self.repository:
            self.repository.append_audit_log(log_entry)
        else:
            self._audit_logs.append(log_entry)
        logger.info(f"Audit: {log_entry}")

    def detect_state_conflict(self, current_listing_state: ListingState, execution_result: ExecutionResult) -> bool:
        """
        Detects if there is a state conflict before syncing.
        For example, if the state is already 'active', we shouldn't apply a new execution over it
        unless it's an update scenario (which we simplify here).
        """
        if current_listing_state in [ListingState.active, ListingState.scheduled] and execution_result.status != "success":
            return True
        return False

    def sync_execution_to_listing(self, execution_result: ExecutionResult, listing_id: str, dry_run: bool = False) -> ListingState:
        current_state = self._get_current_state(listing_id)
        
        if self.detect_state_conflict(current_state, execution_result):
            raise StateConflictError(f"Conflict detected for {listing_id}. Current state: {current_state.value}")

        if execution_result.status == "success":
            new_state = ListingState.active
        elif execution_result.status == "failed":
            new_state = ListingState.pending_retry
        elif execution_result.status == "rolled_back":
            new_state = ListingState.rolled_back
        else:
            new_state = current_state

        if dry_run:
            self._log_audit(listing_id, execution_result.attempt_id, current_state, new_state, "Dry run simulated sync", is_dry_run=True)
            return current_state

        self._update_state(listing_id, new_state)
        self._log_audit(listing_id, execution_result.attempt_id, current_state, new_state, f"Synced execution result {execution_result.status}", is_dry_run=False)
        return new_state

    def handle_execution_failure(self, execution_result: ExecutionResult, listing_id: str, dry_run: bool = False) -> ListingState:
        current_state = self._get_current_state(listing_id)
        new_state = ListingState.pending_retry
        
        if dry_run:
            self._log_audit(listing_id, execution_result.attempt_id, current_state, new_state, "Dry run simulated failure handling", is_dry_run=True)
            return current_state

        self._update_state(listing_id, new_state)
        self._log_audit(listing_id, execution_result.attempt_id, current_state, new_state, "Handled execution failure", is_dry_run=False)
        return new_state

    def handle_rollback(self, attempt_id: str, listing_id: str, dry_run: bool = False) -> ListingState:
        current_state = self._get_current_state(listing_id)
        new_state = ListingState.rolled_back
        
        if dry_run:
            self._log_audit(listing_id, attempt_id, current_state, new_state, "Dry run simulated rollback", is_dry_run=True)
            return current_state

        self._update_state(listing_id, new_state)
        self._log_audit(listing_id, attempt_id, current_state, new_state, "Rolled back state due to execution rollback", is_dry_run=False)
        return new_state
