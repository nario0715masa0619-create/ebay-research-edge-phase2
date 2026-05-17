import os
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from src.admin_web.bootstrap import WebBootstrap
from src.admin_web.context import SellerContextWebResolver

class WebActionGuard:
    @staticmethod
    def check_mutation_allowed(request: Request) -> None:
        """
        Enforces read-only mode and blocks all mutating actions (POST)
        if read-only mode is active in config or environment.
        """
        # Read-only configuration lookup
        read_only_mode = (
            os.environ.get("ADMIN_WEB_READ_ONLY_MODE", "false").lower() == "true" or
            not os.environ.get("ADMIN_WEB_ENABLE_MUTATIONS", "true").lower() == "true"
        )
        
        if read_only_mode:
            raise HTTPException(
                status_code=403,
                detail="Action Blocked: The Administrative Web Interface is running in READ-ONLY mode."
            )

    @staticmethod
    def verify_confirmation(request: Request, form_data: dict) -> None:
        """
        Verifies that explicit user confirmation is present for mutating actions.
        If not confirmed, raises an exception requiring user input.
        """
        require_confirm = os.environ.get("ADMIN_WEB_REQUIRE_CONFIRM_FOR_MUTATIONS", "true").lower() == "true"
        if require_confirm and not form_data.get("confirm") == "true":
            raise HTTPException(
                status_code=400,
                detail="Confirmation Required: You must explicitly confirm this destructive mutation."
            )

    @staticmethod
    def validate_environment_safety(request: Request, action_environment_type: str) -> None:
        """
        Guards against environment mismatch (e.g., executing sandbox actions against production context,
        or publishing listings on environments that do not support live publish).
        """
        active_context = SellerContextWebResolver.resolve(request)
        
        # 1. Environment type boundary check
        if active_context.environment_type != action_environment_type:
            raise HTTPException(
                status_code=400,
                detail=f"Safety Mismatch: Action target environment '{action_environment_type}' does not match active context '{active_context.environment_type}'."
            )
            
        # 2. Production safe guard
        if active_context.environment_type == "production":
            prod_allow = os.environ.get("SELLER_ENV_ALLOW_PRODUCTION_PUBLISH", "false").lower() == "true"
            if not prod_allow and not request.query_params.get("dry_run") == "true":
                # Only block if it is not a dry_run
                raise HTTPException(
                    status_code=403,
                    detail="Safety Block: Production mutation is disabled. Set SELLER_ENV_ALLOW_PRODUCTION_PUBLISH=true to enable."
                )
