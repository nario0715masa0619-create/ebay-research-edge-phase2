import httpx
import logging
from typing import Dict, Any, Optional, List
from src.auth.models import ApiCallContext, TokenInfo
from src.auth.token_service import EbayTokenService
from src.auth.scope_registry import OAuthScopeRegistry
from src.auth.rate_limit import RateLimiter
from src.auth.retry_policy import RetryBackoffPolicy
from src.auth.error_classifier import AuthErrorClassifier

logger = logging.getLogger(__name__)

class EbayBaseApiClient:
    def __init__(self, auth_components: Dict[str, Any]):
        self.auth_service: EbayTokenService = auth_components["token_service"]
        self.scope_registry: OAuthScopeRegistry = auth_components["scope_registry"]
        self.rate_limiter: RateLimiter = auth_components["rate_limiter"]
        self.retry_policy: RetryBackoffPolicy = auth_components["retry_policy"]
        self.error_classifier: AuthErrorClassifier = auth_components["error_classifier"]
        self.config = auth_components["config"]

    def execute_with_auth(
        self, 
        operation_key: str, 
        http_method: str, 
        path: str, 
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        
        # 1. Resolve Scope
        required_scopes = self.scope_registry.get_required_scopes(operation_key)
        seller_id = user_context.get("seller_account_id") if user_context else None
        
        ctx = ApiCallContext(
            operation_key=operation_key,
            http_method=http_method,
            path=path,
            required_scopes=required_scopes,
            seller_account_id=seller_id,
            dry_run=dry_run
        )

        # 2. Rate Limit Acquire
        self.rate_limiter.acquire(operation_key, dry_run=dry_run)

        # 3. Request Loop (Retry Logic)
        for attempt in range(self.config.auth_default_max_retry + 1):
            ctx.retry_count = attempt
            
            # Dry Run Guard
            if dry_run:
                logger.info(f"[DRY RUN] {http_method} {path} with scopes {required_scopes}")
                return {"status_code": 200, "dry_run": True, "operation": operation_key}

            try:
                # 4. Resolve Token
                # Most sell APIs are User tokens. Some might be App tokens.
                # For now, let's assume if scopes start with 'sell', it's User token.
                is_user_api = any("sell" in s for s in required_scopes)
                if is_user_api:
                    token_info = self.auth_service.get_user_access_token(required_scopes, seller_id)
                else:
                    token_info = self.auth_service.get_app_access_token(required_scopes)

                # 5. Execute HTTP Call
                headers = self.auth_service.build_auth_header(token_info)
                url = f"{self.config.ebay_base_api_url}{path}"
                
                response = httpx.request(
                    method=http_method,
                    url=url,
                    headers=headers,
                    json=payload,
                    params=params,
                    timeout=self.config.auth_request_timeout_seconds
                )
                
                if response.is_success:
                    return response.json() if response.content else {"status_code": response.status_code}

                # 6. Error Handling
                error_body = response.json() if response.content else {}
                classification = self.error_classifier.classify(response.status_code, error_body)
                
                if not classification.should_retry or attempt >= self.config.auth_default_max_retry:
                    logger.error(f"Fatal API error: {classification.message}")
                    return {"error": classification.error_code, "status_code": response.status_code, "message": classification.message}

                # 7. Retry Preparation
                if classification.invalidate_token:
                    scope_str = " ".join(sorted(required_scopes))
                    self.auth_service.cache.invalidate(token_info.token_type, scope_str, seller_id)

                # Wait before retry
                backoff = classification.backoff_seconds
                if response.status_code == 429 and "Retry-After" in response.headers:
                    try:
                        backoff = float(response.headers["Retry-After"])
                    except: pass
                
                self.retry_policy.wait(attempt, backoff)
                
            except Exception as e:
                logger.exception(f"Unexpected error in API call: {e}")
                if attempt >= self.config.auth_default_max_retry:
                    return {"error": "unexpected_error", "message": str(e)}
                self.retry_policy.wait(attempt)

        return {"error": "max_retries_exceeded"}
