from typing import Optional, Dict, Any
from .models import AuthFailureInfo

class AuthErrorClassifier:
    def classify(self, status_code: int, error_body: Dict[str, Any]) -> AuthFailureInfo:
        # eBay often returns errors in an 'errors' list or 'error' string for OAuth
        error_type = error_body.get("error", "")
        error_msg = error_body.get("error_description", str(error_body))
        
        # 1. OAuth Endpoint Errors
        if error_type == "invalid_client":
            return AuthFailureInfo(
                error_code="invalid_client",
                category="fatal",
                message="Invalid client credentials",
                retryable_flag=False
            )
        if error_type == "invalid_scope":
            return AuthFailureInfo(
                error_code="invalid_scope",
                category="fatal",
                message="Invalid scope requested",
                retryable_flag=False
            )
        if error_type == "invalid_grant":
            return AuthFailureInfo(
                error_code="invalid_grant",
                category="review_required",
                message="Refresh token might be revoked or invalid",
                retryable_flag=False,
                review_required_flag=True
            )

        # 2. HTTP Status Code Errors
        if status_code == 401:
            return AuthFailureInfo(
                error_code="token_expired",
                category="auth_retryable",
                message="Unauthorized - Token expired or invalid",
                retryable_flag=True
            )
        
        if status_code == 403:
            return AuthFailureInfo(
                error_code="insufficient_scope",
                category="fatal",
                message="Forbidden - Insufficient scope or permissions",
                retryable_flag=False
            )
            
        if status_code == 429:
            return AuthFailureInfo(
                error_code="rate_limited",
                category="rate_limit_retryable",
                message="Rate Limited",
                retryable_flag=True
            )
            
        if 500 <= status_code < 600:
            return AuthFailureInfo(
                error_code="server_error",
                category="retryable",
                message=f"Server Error {status_code}",
                retryable_flag=True
            )
            
        return AuthFailureInfo(
            error_code="fatal_unknown",
            category="fatal",
            message=f"Unknown Error {status_code}: {error_msg}",
            retryable_flag=False
        )
