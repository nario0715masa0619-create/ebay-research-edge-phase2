from typing import Optional, Dict, Any, List
from src.notification.dispatcher import NotificationDispatcher
from src.notification.models import NotificationEvent, NotificationBatchResult
from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository

class NotificationResendService:
    def __init__(self, repository: PersistentNotificationHistoryRepository, dispatcher: NotificationDispatcher):
        self.repository = repository
        self.dispatcher = dispatcher

    def resend_by_history_id(self, history_id: int, dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
        model = self.repository.get_by_history_id(history_id)
        if not model:
            return {"status": "error", "message": f"History ID {history_id} not found."}
            
        event = self._reconstruct_event(model)
        
        batch = self.dispatcher.notify(event, dry_run=dry_run, bypass_checks=force)
        return self._format_batch_result(batch, dry_run)

    def resend_by_event_id(self, event_id: str, channel: str = None, dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
        models = self.repository.get_by_event_id(event_id)
        if not models:
            return {"status": "error", "message": f"Event ID {event_id} not found."}
            
        model = models[0] # Use first one to reconstruct event
        event = self._reconstruct_event(model)
        
        if channel:
            # We need a way to dispatch to a SPECIFIC channel.
            # For simplicity in v0.1 we'll use a rule override or just filter result
            pass

        batch = self.dispatcher.notify(event, dry_run=dry_run, bypass_checks=force)
        return self._format_batch_result(batch, dry_run)

    def _reconstruct_event(self, model) -> NotificationEvent:
        return NotificationEvent(
            event_type=model.event_type,
            title=model.title,
            summary=model.summary,
            event_id=model.event_id,
            source_layer=model.source_layer,
            source_run_id=model.source_run_id,
            sku=model.sku,
            severity=model.severity,
            priority=model.priority,
            meta_json=model.meta_json or {},
            dedupe_key=model.dedupe_key
        )

    def _format_batch_result(self, batch: NotificationBatchResult, dry_run: bool) -> Dict[str, Any]:
        if dry_run:
            return {
                "status": "dry_run",
                "message": "Dry run completed.",
                "dispatched_count": batch.dispatched_count,
                "skipped_count": batch.skipped_count,
                "results": [r.__dict__ for r in batch.results]
            }
        
        return {
            "status": "success" if batch.failed_count == 0 else "partial_failure",
            "dispatched_count": batch.dispatched_count,
            "failed_count": batch.failed_count,
            "results": [r.__dict__ for r in batch.results]
        }
