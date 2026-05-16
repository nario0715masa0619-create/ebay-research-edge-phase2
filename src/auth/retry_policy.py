import time
import math
import random
from typing import Optional
from .config import AuthConfig

class RetryBackoffPolicy:
    def __init__(self, config: AuthConfig):
        self.config = config

    def get_backoff_seconds(self, retry_count: int, explicit_backoff: Optional[float] = None) -> float:
        if explicit_backoff is not None:
            return explicit_backoff
            
        # Exponential backoff: base * 2^retry + jitter
        base = self.config.auth_default_backoff_seconds
        backoff = base * (2 ** retry_count)
        jitter = random.uniform(0, 0.1 * backoff)
        
        final_backoff = min(backoff + jitter, self.config.auth_max_backoff_seconds)
        return final_backoff

    def wait(self, retry_count: int, explicit_backoff: Optional[float] = None):
        wait_time = self.get_backoff_seconds(retry_count, explicit_backoff)
        time.sleep(wait_time)
