from fastapi import Request
from typing import Dict, Any, List
from src.admin_web.bootstrap import WebBootstrap
from src.seller_env.models import SellerContext

class SellerContextWebResolver:
    @staticmethod
    def resolve(request: Request) -> SellerContext:
        container = WebBootstrap.get_container()
        resolver = container.seller_doctor.resolver  # The SellerConfigResolver from context_manager/bootstrap
        
        seller_account_id = request.query_params.get("seller_account_id")
        environment_type = request.query_params.get("environment_type")
        
        # Resolve using our core domain logic
        try:
            return resolver.resolve_context(
                seller_account_id=seller_account_id or None,
                environment_type=environment_type or None
            )
        except Exception as e:
            # Fallback to absolute system default active context if anything fails
            # Let's search if there are any active bindings
            bindings = container.seller_ops.binding_repo.list_all_active()
            if bindings:
                b = bindings[0]
                try:
                    return resolver.resolve_context(b.seller_account_id, None)
                except:
                    pass
            # absolute fallback
            return SellerContext(
                seller_account_id="DEFAULT-SELLER",
                seller_label="Default Seller",
                environment_type="sandbox",
                marketplace_id="EBAY_US",
                currency="USD",
                merchant_location_key="MOCK-LOC",
                fulfillment_policy_id="MOCK-FULFILL",
                payment_policy_id="MOCK-PAY",
                return_policy_id="MOCK-RETURN",
                auth_profile_ref="MOCK-AUTH",
                notification_profile_ref="MOCK-NOTIFY",
                dry_run_default=True,
                publish_enabled=False,
                monitoring_enabled=True,
                sync_enabled=True
            )

class BaseLayoutContextBuilder:
    @staticmethod
    def build(request: Request, current_title: str = "Admin Panel") -> Dict[str, Any]:
        container = WebBootstrap.get_container()
        
        # Resolve active context
        active_context = SellerContextWebResolver.resolve(request)
        
        # Retrieve lists of all enabled sellers and environment profiles for headers
        all_sellers = container.seller_ops.seller_repo.list_all(enabled_only=True)
        all_envs = container.seller_ops.env_repo.list_all(enabled_only=True)
        
        # Construct parameters for easy propagation in links/forms
        context_params = {
            "seller_account_id": active_context.seller_account_id,
            "environment_type": active_context.environment_type
        }
        
        # Flash messages retrieval from signed session cookies
        flash_messages = []
        if hasattr(request, "session") and "flash" in request.session:
            flash_messages = request.session.pop("flash")
            
        return {
            "request": request,
            "title": f"{current_title} - {active_context.seller_label}",
            "active_context": active_context,
            "all_sellers": all_sellers,
            "all_envs": all_envs,
            "context_params": context_params,
            "flash_messages": flash_messages,
            "read_only_mode": getattr(container, "read_only_mode", False)
        }
