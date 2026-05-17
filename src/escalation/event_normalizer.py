from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class NormalizedEscalationEvent:
    source_event_id: str
    source_history_id: Optional[str]
    source_event_type: str
    seller_account_id: Optional[str]
    environment_type: Optional[str]
    sku: Optional[str]
    dedupe_key: str
    severity: str
    priority: str
    payload: Dict[str, Any]

class EscalationEventNormalizer:
    @staticmethod
    def normalize_notification_history(history: Any) -> NormalizedEscalationEvent:
        payload = history.meta_json or {}
        event_type = history.event_type
        seller_account_id = history.seller_account_id
        environment_type = history.environment_type
        sku = payload.get("sku") or payload.get("item_id")
        
        # Determine source logical key
        logical_key = history.event_id
        if "job_name" in payload:
            logical_key = payload["job_name"]
        elif "doctor_check_name" in payload:
            logical_key = payload["doctor_check_name"]
        elif sku:
            logical_key = sku
            
        dedupe_key = f"{event_type}:{seller_account_id or 'none'}:{environment_type or 'none'}:{sku or 'none'}:{logical_key}"
        
        return NormalizedEscalationEvent(
            source_event_id=history.event_id,
            source_history_id=history.event_id,
            source_event_type=event_type,
            seller_account_id=seller_account_id,
            environment_type=environment_type,
            sku=sku,
            dedupe_key=dedupe_key,
            severity=history.severity or "warning",
            priority=payload.get("priority") or "medium",
            payload=payload
        )

    @staticmethod
    def normalize_job_run(job_run: Any) -> NormalizedEscalationEvent:
        event_type = "scheduled_job_failed"
        seller_account_id = job_run.seller_account_id
        environment_type = job_run.environment_type
        job_name = job_run.job_name
        
        dedupe_key = f"{event_type}:{seller_account_id or 'none'}:{environment_type or 'none'}:none:{job_name}"
        
        payload = {
            "job_name": job_name,
            "run_id": job_run.run_id,
            "error_message": job_run.error_summary,
            "started_at": job_run.started_at.isoformat() if job_run.started_at else None,
            "completed_at": job_run.finished_at.isoformat() if job_run.finished_at else None,
        }
        
        return NormalizedEscalationEvent(
            source_event_id=job_run.run_id,
            source_history_id=None,
            source_event_type=event_type,
            seller_account_id=seller_account_id,
            environment_type=environment_type,
            sku=None,
            dedupe_key=dedupe_key,
            severity="error",
            priority="high",
            payload=payload
        )

    @staticmethod
    def normalize_monitoring_event(mon_event: Any) -> NormalizedEscalationEvent:
        event_type = mon_event.event_type
        seller_account_id = mon_event.seller_account_id
        environment_type = mon_event.environment_id
        sku = mon_event.sku
        
        dedupe_key = f"{event_type}:{seller_account_id or 'none'}:{environment_type or 'none'}:{sku or 'none'}:{sku}"
        
        payload = mon_event.payload_json or {}
        
        return NormalizedEscalationEvent(
            source_event_id=mon_event.event_id,
            source_history_id=None,
            source_event_type=event_type,
            seller_account_id=seller_account_id,
            environment_type=environment_type,
            sku=sku,
            dedupe_key=dedupe_key,
            severity="warning",
            priority="medium",
            payload=payload
        )
