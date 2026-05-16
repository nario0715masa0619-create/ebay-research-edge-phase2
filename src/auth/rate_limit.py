import time
import threading
from typing import Dict, Optional
from .config import AuthConfig

class RateLimiter:
    def __init__(self, config: AuthConfig):
        self.config = config
        self._lock = threading.Lock()
        # Operation Key -> (Last Request Time, Available Tokens)
        # Simple Token Bucket implementation
        self._buckets: Dict[str, Dict[str, float]] = {}

    def acquire(self, operation_key: str, dry_run: bool = False):
        if dry_run or not self.config.auth_enable_rate_limit:
            return

        with self._lock:
            bucket = self._buckets.get(operation_key)
            if not bucket:
                bucket = {
                    "last_time": time.time(),
                    "tokens": float(self.config.rate_limit_default_burst)
                }
                self._buckets[operation_key] = bucket

            now = time.time()
            elapsed = now - bucket["last_time"]
            
            # Refill
            refill_rate = self.config.rate_limit_default_rps
            bucket["tokens"] = min(
                float(self.config.rate_limit_default_burst),
                bucket["tokens"] + elapsed * refill_rate
            )
            bucket["last_time"] = now

            if bucket["tokens"] < 1.0:
                # Need to wait
                wait_time = (1.0 - bucket["tokens"]) / refill_rate
                time.sleep(wait_time)
                # Recurse after sleep or just adjust tokens
                bucket["tokens"] = 0.0
                bucket["last_time"] = time.time()
            else:
                bucket["tokens"] -= 1.0

    def cooldown(self, seconds: Optional[int] = None):
        wait = seconds or self.config.rate_limit_429_cooldown_seconds
        time.sleep(wait)
