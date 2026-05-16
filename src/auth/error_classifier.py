from typing import Optional, Dict, Any
from .models import AuthErrorClassification

class AuthErrorClassifier:
    def classify(self, status_code: int, error_body: Dict[str, Any]) -> AuthErrorClassification:
        error_msg = str(error_body)
        
        if status_code == 401:
            return AuthErrorClassification(
                error_code="token_expired_or_invalid",
                category="auth_retryable",
                message="Unauthorized - Token might be expired",
                should_retry=True,
                invalidate_token=True
            )
        
        if status_code == 403:
            return AuthErrorClassification(
                error_code="insufficient_scope_or_permission",
                category="fatal",
                message="Forbidden - Insufficient scope or permissions",
                should_retry=False
            )
            
        if status_code == 429:
            return AuthErrorClassification(
                error_code="rate_limited",
                category="rate_limit_retryable",
                message="Rate Limited - Too many requests",
                should_retry=True,
                backoff_seconds=None  # Should use Retry-After header if available
            )
            
        if 500 <= status_code < 600:
            return AuthErrorClassification(
                error_code="server_error",
                category="retryable",
                message=f"Server Error {status_code}",
                should_retry=True
            )
            
        return AuthErrorClassification(
            error_code="unknown_error",
            category="fatal",
            message=f"Error {status_code}: {error_msg}",
            should_retry=False
        )
