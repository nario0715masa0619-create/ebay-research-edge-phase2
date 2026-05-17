from datetime import datetime
from typing import Tuple, Optional
from src.escalation.models import EscalationState, EscalationPolicy

def evaluate_sla_breach(state: EscalationState, policy: EscalationPolicy, now: datetime) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates if the state has breached the SLA target defined in the policy.
    Returns (is_breached, target_severity, target_priority)
    """
    if state.current_status == "resolved" or state.current_status == "closed":
        return False, None, None

    # Use state's override SLA if available, else policy SLA
    sla_seconds = state.sla_target_seconds if state.sla_target_seconds is not None else policy.sla_target_seconds

    if sla_seconds is None:
        return False, None, None

    aging_seconds = int((now - state.first_seen_at).total_seconds())

    if aging_seconds >= sla_seconds:
        # It's breached!
        return True, policy.sla_breach_severity, policy.sla_breach_priority

    return False, None, None
