import logging
from typing import List, Optional
from src.seller_env.models import SellerContext

logger = logging.getLogger(__name__)

class EnvironmentGuard:
    def __init__(self, strict_match: bool = True):
        self.strict_match = strict_match

    def validate_execution(self, context: SellerContext, action_type: str = "read"):
        """
        Validates if the current context allows the specified action.
        """
        if not context.seller_account_id:
            raise ValueError("Seller account ID missing in context.")
            
        if not context.environment_type:
            raise ValueError("Environment type missing in context.")

        if action_type == "publish":
            if not context.publish_enabled:
                raise PermissionError(f"Publish is not enabled for environment {context.environment_type}")
            
            # Additional safety: ensure required IDs are present
            required_ids = [
                context.fulfillment_policy_id,
                context.payment_policy_id,
                context.return_policy_id,
                context.merchant_location_key
            ]
            if any(id is None for id in required_ids):
                raise ValueError("Missing required policy or location IDs for publish.")

    def check_auth_integration(self, context: SellerContext, api_url: str):
        """
        Ensures the API endpoint matches the environment type.
        """
        is_sandbox_url = "sandbox" in api_url.lower()
        is_sandbox_env = context.environment_type == "sandbox"
        
        if is_sandbox_env != is_sandbox_url:
            raise RuntimeError(
                f"Environment mismatch detected! Environment is {context.environment_type} "
                f"but API URL is {api_url}"
            )
            
    def check_seller_binding(self, seller_id: str, env_type: str, binding_env_id: str):
        # Verification that the binding matches expected environment
        pass
