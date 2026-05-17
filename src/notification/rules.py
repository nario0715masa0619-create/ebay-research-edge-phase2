from typing import List
from .models import NotificationRule

def get_default_notification_rules() -> List[NotificationRule]:
    return [
        NotificationRule(
            rule_name="Auth Critical",
            event_types=["auth_refresh_failed", "invalid_grant_detected"],
            severities=["critical"],
            channel_targets=["console", "slack", "email", "webhook"],
            cooldown_seconds=300
        ),
        NotificationRule(
            rule_name="Job Failure",
            event_types=["scheduled_job_failed"],
            severities=["error"],
            channel_targets=["console", "slack", "webhook"],
            cooldown_seconds=60
        ),
        NotificationRule(
            rule_name="Drift Warning",
            event_types=["listing_drift_detected"],
            severities=["warning"],
            channel_targets=["console", "slack"],
            cooldown_seconds=1800
        ),
        NotificationRule(
            rule_name="Review Required",
            event_types=["scheduled_job_completed_with_reviews"],
            severities=["info"],
            channel_targets=["console", "slack"],
            review_required_flag=True
        ),
        NotificationRule(
            rule_name="Doctor Failure",
            event_types=["doctor_check_failed"],
            severities=["error", "warning"],
            channel_targets=["console", "slack"],
            cooldown_seconds=300
        )
    ]
