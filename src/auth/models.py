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
    source_type: str = "mint" # 'mint', 'refresh', 'cache'

    def is_expired(self, lead_seconds: int = 0) -> bool:
        return datetime.now().timestamp() + lead_seconds > self.expires_at.timestamp()

@dataclass
class TokenRequestContext:
    operation_key: str
    scopes: List[str]
    seller_account_id: Optional[str] = None
    force_refresh: bool = False
    environment: str = "sandbox"

@dataclass
class AuthResult:
    success: bool
    token_info: Optional[TokenInfo] = None
    failure_info: Optional['AuthFailureInfo'] = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RateLimitDecision:
    allowed: bool
    wait_seconds: float = 0.0
    reason: Optional[str] = None
    observed_retry_after: Optional[float] = None

@dataclass
class RetryDecision:
    should_retry: bool
    backoff_seconds: float = 0.0
    next_attempt_number: int = 0
    reason: Optional[str] = None

@dataclass
class AuthFailureInfo:
    error_code: str
    category: str  # 'auth_retryable', 'rate_limit_retryable', 'fatal', 'review_required'
    message: str
    reason_codes: List[str] = field(default_factory=list)
    retryable_flag: bool = False
    review_required_flag: bool = False
    invalidate_token_flag: bool = False

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
