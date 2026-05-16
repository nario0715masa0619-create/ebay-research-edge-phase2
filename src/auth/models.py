from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class TokenInfo:
    token_type: str  # 'Application' or 'User'
    access_token: str
    expires_at: datetime
    refresh_token: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    seller_account_id: Optional[str] = None
    environment: str = "sandbox"

    def is_expired(self, lead_seconds: int = 0) -> bool:
        return datetime.now().timestamp() + lead_seconds > self.expires_at.timestamp()

@dataclass
class ApiCallContext:
    operation_key: str
    http_method: str
    path: str
    required_scopes: List[str] = field(default_factory=list)
    seller_account_id: Optional[str] = None
    dry_run: bool = False
    retry_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)

@dataclass
class RateLimitSnapshot:
    operation_key: str
    limit: int
    remaining: int
    reset_at: datetime
    window_seconds: int

@dataclass
class AuthErrorClassification:
    error_code: str
    category: str  # 'auth_retryable', 'rate_limit_retryable', 'fatal', 'review_required'
    message: str
    should_retry: bool = False
    backoff_seconds: Optional[float] = None
    invalidate_token: bool = False
