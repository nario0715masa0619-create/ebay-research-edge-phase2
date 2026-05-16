from typing import Dict, Any, List
from .models import ScheduledJobResult

class JobRetryPlanner:
    """
    Decides whether to retry a failed job based on its result and retry counts.
    """
    def should_retry(self, result: ScheduledJobResult, retry_count: int, max_retry: int) -> bool:
        if result.success_flag:
            return False
        
        if retry_count >= max_retry:
            return False

        # In v0.1, we retry if there are retryable errors or if it failed with a potentially transient error
        if result.retryable_error_count > 0:
            return True
            
        if result.status in ["failed", "timed_out"] and not result.fatal_error_count > 0:
            return True

        return False

    def get_retry_delay(self, retry_count: int, base_delay: int) -> int:
        return base_delay * (2 ** retry_count) # Exponential backoff
