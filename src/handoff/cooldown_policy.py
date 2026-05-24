from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from src.handoff.config import HandoffSettings

class CooldownPolicy:
    def __init__(self, settings: HandoffSettings):
        self.settings = settings

    def check_cooldown(self, last_seller_execution_at: Optional[datetime], now: datetime = None) -> Tuple[bool, Optional[datetime], Optional[str]]:
        """
        Returns:
            Tuple[is_in_cooldown, next_retry_at, reason]
        """
        if last_seller_execution_at is None:
            return False, None, None
            
        if now is None:
            now = datetime.utcnow()
            
        last_aware = last_seller_execution_at.replace(tzinfo=timezone.utc) if last_seller_execution_at.tzinfo is None else last_seller_execution_at
        now_aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
        
        elapsed_seconds = (now_aware - last_aware).total_seconds()
        
        if elapsed_seconds < self.settings.seller_cooldown_seconds:
            remaining_seconds = self.settings.seller_cooldown_seconds - elapsed_seconds
            next_retry_at = now_aware + timedelta(seconds=remaining_seconds)
            return True, next_retry_at, f"Seller is in cooldown. {int(remaining_seconds)}s remaining."
            
        return False, None, None
