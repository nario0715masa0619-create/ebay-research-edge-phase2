import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from src.listing_execution.gateways.execution_gateway import ExecutionResult
from src.monitoring.models.alert import Alert, AlertLevel

logger = logging.getLogger(__name__)

class ExecutionMonitor:
    def __init__(self, repository=None):
        self.repository = repository
        self._audit_logs = []
        self._alert_history = set()  # Using set of attempt_ids for idempotency

    def classify_failure(self, failure_boundary: str, retry_count: int, max_attempts: int = 3) -> AlertLevel:
        if failure_boundary == "STATE_CONFLICT":
            return AlertLevel.CRITICAL
        if retry_count >= max_attempts:
            return AlertLevel.CRITICAL
        if failure_boundary == "SELLER_LIMIT":
            return AlertLevel.WARNING
        if failure_boundary == "UNKNOWN":
            return AlertLevel.WARNING
        if failure_boundary in ["TIMEOUT", "NETWORK_ERROR"]:
            return AlertLevel.INFO
        
        return AlertLevel.WARNING

    def should_alert(self, execution_result: ExecutionResult) -> bool:
        if execution_result.status != "failed":
            return False
        if execution_result.attempt_id in self._alert_history:
            return False
        return True

    def detect_failure(self, execution_result: ExecutionResult, listing_id: str, attempt_history: Dict[str, Any] = None) -> Alert:
        if not attempt_history:
            attempt_history = {
                "failure_boundary": "UNKNOWN",
                "retry_count": 0,
                "max_attempts": 3,
                "next_retry_at": None,
                "deferred_until": None,
                "is_cancelled": False
            }

        failure_boundary = attempt_history.get("failure_boundary", "UNKNOWN")
        retry_count = attempt_history.get("retry_count", 0)
        max_attempts = attempt_history.get("max_attempts", 3)
        
        alert_level = self.classify_failure(failure_boundary, retry_count, max_attempts)

        # Message construction based on retry/defer/cancel
        if attempt_history.get("is_cancelled") or alert_level == AlertLevel.CRITICAL:
            message = "Cancelling execution"
        elif attempt_history.get("deferred_until"):
            message = f"Deferred until {attempt_history.get('deferred_until')}"
        elif attempt_history.get("next_retry_at"):
            message = f"Will retry at {attempt_history.get('next_retry_at')}"
        else:
            message = "Execution failed"

        reason = execution_result.error_reason or "No reason provided"

        alert = Alert(
            listing_id=listing_id,
            attempt_id=execution_result.attempt_id,
            failure_boundary=failure_boundary,
            alert_level=alert_level,
            message=message,
            reason=reason
        )
        return alert

    def log_alert(self, alert: Alert, dry_run: bool = False):
        if dry_run:
            log_entry = {
                "alert_id": alert.alert_id,
                "action": "skip",
                "reason": "dry_run=true"
            }
            self._audit_logs.append(log_entry)
            logger.info(f"Dry run alert skip: {alert}")
            return
            
        alert.alert_sent_at = datetime.now(timezone.utc)
        log_entry = {
            "alert_id": alert.alert_id,
            "action": "sent",
            "alert_level": alert.alert_level.value,
            "attempt_id": alert.attempt_id,
            "listing_id": alert.listing_id
        }
        self._audit_logs.append(log_entry)
        self._alert_history.add(alert.attempt_id)
        
        if self.repository:
            self.repository.save_alert(alert)
            self.repository.append_audit_log(log_entry)
            
        logger.info(f"Alert sent: {alert}")

    def process_execution_result(self, execution_result: ExecutionResult, listing_id: str, attempt_history: Dict[str, Any] = None, dry_run: bool = False):
        if not self.should_alert(execution_result):
            return None
            
        alert = self.detect_failure(execution_result, listing_id, attempt_history)
        self.log_alert(alert, dry_run=dry_run)
        return alert
