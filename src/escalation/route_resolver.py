from typing import List, Optional
from src.escalation.models import EscalationState, EscalationPolicy

class RouteResolver:
    def __init__(self, default_sandbox_routes: List[str] = ["console_only"]):
        self.default_sandbox_routes = default_sandbox_routes

    def resolve(self, state: EscalationState, policy: EscalationPolicy, base_routes: List[str]) -> List[str]:
        """
        Determines the final notification routes for an escalation/reminder.
        Ensures sandbox environments do not spam production channels.
        Applies policy-level route overrides if available.
        """
        routes = list(base_routes)

        if policy.route_override_key:
            # Simple override simulation based on the key
            routes.append(policy.route_override_key)

        if state.sla_breached_at:
            # If breached, we might want to ensure a critical channel is present
            if "email_critical" not in routes:
                routes.append("email_critical")

        if state.environment_type == "sandbox":
            # Force sandbox routes (prevent real Slack/Email if not explicitly configured for sandbox)
            return self.default_sandbox_routes
            
        # Ensure uniqueness
        return list(set(routes))
