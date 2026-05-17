from typing import List

class SellerNotificationRouteResolver:
    def __init__(self, resolver):
        self.resolver = resolver

    def resolve_channels(self, event, base_channels: List[str]) -> List[str]:
        if not event.seller_account_id:
            return base_channels
            
        try:
            ctx = self.resolver.resolve_context(event.seller_account_id, event.environment_type)
            
            # If environment is sandbox, route only to console for non-critical alerts
            if ctx.environment_type == "sandbox":
                if getattr(event, "severity", "info") != "critical":
                    return ["console"]
            
            # Custom channel routing defined in binding
            binding = self.resolver._find_binding_by_type(ctx.seller_account_id, ctx.environment_type)
            if binding and binding.notification_channel_profile:
                return [c.strip() for c in binding.notification_channel_profile.split(",")]
                
        except Exception:
            pass
            
        return base_channels
