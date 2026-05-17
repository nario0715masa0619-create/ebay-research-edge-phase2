from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.escalation.models import EscalationState, EscalationPolicy
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository, PersistentEscalationPolicyRepository

from src.escalation.bulk_action_service import BulkActionService
from src.escalation.note_service import NoteService
from src.escalation.timeline_builder import TimelineBuilder
from src.escalation.metrics_service import MetricsService
from src.escalation.maintenance_window_service import MaintenanceWindowService
from src.escalation.models import MaintenanceWindow

class EscalationOpsService:
    def __init__(
        self, 
        state_repo: PersistentEscalationStateRepository, 
        policy_repo: PersistentEscalationPolicyRepository,
        bulk_action_service: BulkActionService = None,
        note_service: NoteService = None,
        timeline_builder: TimelineBuilder = None,
        metrics_service: MetricsService = None,
        maintenance_service: MaintenanceWindowService = None
    ):
        self.state_repo = state_repo
        self.policy_repo = policy_repo
        self.bulk_action_service = bulk_action_service
        self.note_service = note_service
        self.timeline_builder = timeline_builder
        self.metrics_service = metrics_service
        self.maintenance_service = maintenance_service

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        states = self.state_repo.list_recent(limit=limit)
        return [self._format_state(s) for s in states]

    def list_active(self) -> List[Dict[str, Any]]:
        states = []
        for status in ["open", "acknowledged", "escalated"]:
            states.extend(self.state_repo.list_by_status(status))
        # Sort by updated_at desc
        states.sort(key=lambda s: s.updated_at, reverse=True)
        return [self._format_state(s) for s in states]

    def get_details(self, state_id: str) -> Optional[Dict[str, Any]]:
        state = self.state_repo.get_by_state_id(state_id)
        return self._format_state(state) if state else None

    def ack(self, state_id: str, actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success = self.state_repo.mark_acknowledged(state_id, actor_id, note)
        return {"status": "success" if success else "failed", "state_id": state_id, "action": "acknowledge"}

    def resolve(self, state_id: str, actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success = self.state_repo.mark_resolved(state_id, actor_id, note)
        return {"status": "success" if success else "failed", "state_id": state_id, "action": "resolve"}

    def silence(self, state_id: str, hours: int, actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        silenced_until = datetime.now() + timedelta(hours=hours)
        success = self.state_repo.mark_silenced(state_id, silenced_until, actor_id, note)
        return {"status": "success" if success else "failed", "state_id": state_id, "action": "silence", "silenced_until": silenced_until.isoformat()}
        
    def unsilence(self, state_id: str, actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success = self.state_repo.clear_silence(state_id, actor_id, note)
        return {"status": "success" if success else "failed", "state_id": state_id, "action": "unsilence"}

    def stats(self) -> Dict[str, Any]:
        if self.metrics_service:
            snapshot = self.metrics_service.get_snapshot()
            return {
                "unresolved": snapshot.unresolved_total,
                "breached": snapshot.breached_total,
                "re_escalated": snapshot.re_escalation_total,
                "aging_buckets": snapshot.aging_bucket_counts,
                "seller_counts": snapshot.seller_counts,
                "env_counts": snapshot.environment_counts,
                "avg_ack_s": snapshot.avg_time_to_ack_seconds,
                "avg_resolve_s": snapshot.avg_time_to_resolve_seconds
            }
        return self.state_repo.list_stats()
        
    def list_policies(self) -> List[Dict[str, Any]]:
        policies = self.policy_repo.list_enabled()
        return [self._format_policy(p) for p in policies]

    def _format_state(self, state: EscalationState) -> Dict[str, Any]:
        return {
            "state_id": state.state_id,
            "event_type": state.source_event_type,
            "seller_account_id": state.seller_account_id,
            "environment_type": state.environment_type,
            "status": state.current_status,
            "severity": state.current_severity,
            "priority": state.current_priority,
            "reminder_count": state.reminder_count,
            "escalation_level": state.escalation_level,
            "first_seen": state.first_seen_at.isoformat() if state.first_seen_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
            "silenced_until": state.silenced_until.isoformat() if state.silenced_until else None,
            "resolved_at": state.resolved_at.isoformat() if state.resolved_at else None,
            "aging_bucket": state.aging_bucket,
            "sla_breached": True if state.sla_breached_at else False,
            "re_escalation_count": state.re_escalation_count
        }

    def _format_policy(self, policy: EscalationPolicy) -> Dict[str, Any]:
        return {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "event_type": policy.event_type,
            "seller_account_id": policy.seller_account_id,
            "environment_type": policy.environment_type,
            "reminder_enabled": policy.reminder_enabled,
            "reminder_interval": policy.reminder_interval_seconds,
            "reminder_max": policy.reminder_max_count,
            "escalation_enabled": policy.escalation_enabled,
            "steps": len(policy.escalation_steps) if policy.escalation_steps else 0,
            "v0.2_enabled": policy.re_escalation_enabled or bool(policy.sla_target_seconds)
        }

    # --- v0.2 Extensions ---
    def list_breached(self) -> List[Dict[str, Any]]:
        states = self.state_repo.list_breached()
        return [self._format_state(s) for s in states]

    def list_aging(self, bucket: str) -> List[Dict[str, Any]]:
        states = self.state_repo.list_by_aging_bucket(bucket)
        return [self._format_state(s) for s in states]

    def add_note(self, state_id: str, body: str, actor_id: str) -> Dict[str, Any]:
        note = self.note_service.add_note(state_id, body, actor_id)
        return {"note_id": note.note_id, "status": "success"}

    def list_notes(self, state_id: str) -> List[Dict[str, Any]]:
        notes = self.note_service.list_notes(state_id)
        return [{"note_id": n.note_id, "body": n.body, "author": n.author_id, "created_at": n.created_at.isoformat()} for n in notes]

    def timeline(self, state_id: str) -> List[Dict[str, Any]]:
        items = self.timeline_builder.build_timeline(state_id)
        return [{"type": i.item_type, "timestamp": i.timestamp.isoformat(), "actor": i.actor, "description": i.description} for i in items]

    def bulk_ack(self, state_ids: List[str], actor_id: str) -> Dict[str, Any]:
        return self.bulk_action_service.bulk_ack(state_ids, actor_id)

    def bulk_resolve(self, state_ids: List[str], actor_id: str) -> Dict[str, Any]:
        return self.bulk_action_service.bulk_resolve(state_ids, actor_id)

    def bulk_silence(self, state_ids: List[str], hours: int, actor_id: str) -> Dict[str, Any]:
        silenced_until = datetime.now() + timedelta(hours=hours)
        return self.bulk_action_service.bulk_silence(state_ids, silenced_until, actor_id)

    def maintenance_list(self) -> List[Dict[str, Any]]:
        windows = self.maintenance_service.repository.list_all()
        return [{"window_id": w.window_id, "enabled": w.enabled, "starts": w.starts_at.isoformat(), "ends": w.ends_at.isoformat(), "action": w.action} for w in windows]

    def maintenance_add(self, starts_at: datetime, ends_at: datetime, action: str, seller_account_id: Optional[str] = None, env: Optional[str] = None, event: Optional[str] = None) -> Dict[str, Any]:
        w = MaintenanceWindow(
            window_id="", seller_account_id=seller_account_id, environment_type=env, event_type=event,
            enabled=True, starts_at=starts_at, ends_at=ends_at, action=action
        )
        res = self.maintenance_service.repository.save(w)
        return {"window_id": res.window_id, "status": "success"}

    def maintenance_remove(self, window_id: str) -> Dict[str, Any]:
        success = self.maintenance_service.repository.remove(window_id)
        return {"status": "success" if success else "failed"}
