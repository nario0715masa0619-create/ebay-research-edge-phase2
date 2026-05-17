from typing import List, Dict, Any
from src.escalation.models import EscalationPolicy, EscalationStep

DEFAULT_POLICIES: List[EscalationPolicy] = [
    EscalationPolicy(
        policy_id="default_auth_refresh_failed",
        name="Default Auth Refresh Failed Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="auth_refresh_failed",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=300,
        reminder_max_count=10,
        allow_reminder_after_ack=True,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True,
        escalation_steps=[
            EscalationStep(
                step_index=1,
                after_seconds=900,
                min_repeat_count=1,
                target_severity="critical",
                target_priority="high",
                target_channels=["slack", "webhook"],
                cooldown_seconds=300,
                require_unacked=False,
                note="Escalate to critical and alert Slack and Webhook channels."
            ),
            EscalationStep(
                step_index=2,
                after_seconds=1800,
                min_repeat_count=2,
                target_severity="critical",
                target_priority="critical",
                target_channels=["slack", "webhook", "email"],
                cooldown_seconds=600,
                require_unacked=False,
                note="Escalate further and send out direct Email notification."
            )
        ],
        dedupe_scope="seller_env"
    ),
    EscalationPolicy(
        policy_id="default_scheduled_job_failed",
        name="Default Scheduled Job Failed Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="scheduled_job_failed",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=900,
        reminder_max_count=5,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True,
        escalation_steps=[
            EscalationStep(
                step_index=1,
                after_seconds=1800,
                min_repeat_count=1,
                target_severity="error",
                target_priority="high",
                target_channels=["slack"],
                cooldown_seconds=300,
                require_unacked=True,
                note="Escalate unacknowledged job failures to Slack."
            ),
            EscalationStep(
                step_index=2,
                after_seconds=3600,
                min_repeat_count=2,
                target_severity="critical",
                target_priority="high",
                target_channels=["slack", "webhook"],
                cooldown_seconds=600,
                require_unacked=True,
                note="Escalate long-running unacknowledged job failures to Webhook."
            )
        ],
        dedupe_scope="seller_env_job"
    ),
    EscalationPolicy(
        policy_id="default_listing_drift_detected",
        name="Default Listing Drift Detected Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="listing_drift_detected",
        base_severity="warning",
        reminder_enabled=True,
        reminder_interval_seconds=1800,
        reminder_max_count=3,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True,
        escalation_steps=[
            EscalationStep(
                step_index=1,
                after_seconds=7200,
                min_repeat_count=1,
                target_severity="error",
                target_priority="medium",
                target_channels=["slack"],
                cooldown_seconds=1800,
                require_unacked=True,
                note="Escalate unacknowledged listing drifts to Slack after 2 hours."
            )
        ],
        dedupe_scope="seller_env_sku"
    ),
    EscalationPolicy(
        policy_id="default_doctor_check_failed",
        name="Default Doctor Check Failed Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="doctor_check_failed",
        base_severity="warning",
        reminder_enabled=True,
        reminder_interval_seconds=3600,
        reminder_max_count=2,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True,
        escalation_steps=[
            EscalationStep(
                step_index=1,
                after_seconds=14400,
                min_repeat_count=1,
                target_severity="error",
                target_priority="medium",
                target_channels=["email"],
                cooldown_seconds=3600,
                require_unacked=True,
                note="Escalate unacknowledged doctor failures to Email after 4 hours."
            )
        ],
        dedupe_scope="seller_env_doctor"
    )
]

def get_system_default_policy(event_type: str, severity: str = "warning") -> EscalationPolicy:
    # Safe system default policy fallback in case no custom/default policy matches
    return EscalationPolicy(
        policy_id=f"fallback_system_{event_type}",
        name=f"System Fallback for {event_type}",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type=event_type,
        base_severity=severity,
        reminder_enabled=True,
        reminder_interval_seconds=3600,
        reminder_max_count=3,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False,
        escalation_steps=[],
        dedupe_scope="default"
    )
