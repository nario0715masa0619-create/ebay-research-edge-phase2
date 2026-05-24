from typing import Tuple, Optional
from src.handoff.config import HandoffSettings

class CapacityController:
    def __init__(self, settings: HandoffSettings):
        self.settings = settings

    def check_capacity(self, run_handoff_count: int, seller_active_execution_count: int) -> Tuple[bool, bool, Optional[str]]:
        """
        Returns:
            Tuple[capacity_allowed, should_defer, capacity_reason]
        """
        if run_handoff_count >= self.settings.max_per_run:
            if self.settings.defer_when_capacity_full:
                return False, True, f"Max handoffs per run ({self.settings.max_per_run}) reached."
            else:
                return False, False, f"Max handoffs per run ({self.settings.max_per_run}) reached. Defer disabled."
                
        if seller_active_execution_count >= self.settings.max_per_seller:
            if self.settings.defer_when_capacity_full:
                return False, True, f"Seller active execution count ({seller_active_execution_count}) reached limit ({self.settings.max_per_seller})."
            else:
                return False, False, f"Seller active execution count ({seller_active_execution_count}) reached limit. Defer disabled."
                
        return True, False, None
