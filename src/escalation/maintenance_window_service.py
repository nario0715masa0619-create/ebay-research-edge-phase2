from datetime import datetime
from typing import Optional, List
from src.escalation.models import MaintenanceWindow, EscalationState
from src.repositories.persistent_maintenance_window_repository import PersistentMaintenanceWindowRepository

class MaintenanceWindowService:
    def __init__(self, repository: PersistentMaintenanceWindowRepository):
        self.repository = repository

    def evaluate_suppression(self, state: EscalationState, now: datetime) -> Optional[MaintenanceWindow]:
        """
        Returns the applicable MaintenanceWindow if the state should be suppressed at this time, otherwise None.
        """
        windows = self.repository.resolve_applicable_windows(
            now=now,
            seller_account_id=state.seller_account_id,
            environment_type=state.environment_type,
            event_type=state.source_event_type
        )
        
        if not windows:
            return None
            
        # Return the most restrictive / highest priority window. 
        # For simplicity, returning the first one.
        return windows[0]
