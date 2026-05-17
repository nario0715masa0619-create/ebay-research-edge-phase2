from datetime import datetime
from src.escalation.models import EscalationState, EscalationPolicy

class ReEscalationDecisionEngine:
    def evaluate(self, state: EscalationState, policy: EscalationPolicy, now: datetime) -> str:
        """
        Returns 're_escalate', 'skip_maxed_out', 'skip_interval_not_met', 'skip_not_enabled', 'skip_resolved', 'skip_not_escalated'
        """
        if state.current_status == "resolved" or state.current_status == "closed":
            return "skip_resolved"
            
        if state.escalation_level == 0 and not state.last_escalated_at:
            # Has not been escalated initially yet
            return "skip_not_escalated"

        if not policy.re_escalation_enabled:
            return "skip_not_enabled"

        if policy.re_escalation_max_count is not None and state.re_escalation_count >= policy.re_escalation_max_count:
            return "skip_maxed_out"

        interval = policy.re_escalation_interval_seconds or 3600
        
        last_action_at = state.last_re_escalated_at or state.last_escalated_at
        if not last_action_at:
            return "re_escalate" # Should not happen based on state checks, but fail-safe

        seconds_since = (now - last_action_at).total_seconds()
        
        if seconds_since >= interval:
            return "re_escalate"
            
        return "skip_interval_not_met"
