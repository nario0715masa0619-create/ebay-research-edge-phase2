import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import Session

from src.db.models import (
    EscalationStateModel,
    EscalationStateTransitionModel,
    EscalationPolicyModel
)
from src.escalation.models import (
    EscalationState,
    EscalationStateTransition,
    EscalationPolicy,
    EscalationStep
)

class PersistentEscalationStateRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_open_state(self, state: EscalationState) -> EscalationState:
        stmt = select(EscalationStateModel).where(EscalationStateModel.dedupe_key == state.dedupe_key)
        model = self.session.execute(stmt).scalar_one_or_none()

        if model:
            # Reopen or update last seen if already resolved or open
            if model.resolved_at is not None:
                # Reopen resolved issue
                model.resolved_at = None
                model.resolved_by = None
                model.resolution_note = None
                model.current_status = "open"
                model.reminder_count = 0
                model.escalation_level = 0
            
            model.last_seen_at = state.last_seen_at or datetime.now()
            model.source_event_id = state.source_event_id
            model.source_history_id = state.source_history_id
            model.source_status_snapshot = state.source_status_snapshot
            model.updated_at = datetime.now()
            
            # Update v0.2 fields if passed in state
            model.aging_seconds = state.aging_seconds
            model.aging_bucket = state.aging_bucket
            model.sla_target_seconds = state.sla_target_seconds
            model.sla_breached_at = state.sla_breached_at
            model.sla_breach_count = state.sla_breach_count
            model.re_escalation_count = state.re_escalation_count
            model.last_re_escalated_at = state.last_re_escalated_at
            model.maintenance_suppressed_until = state.maintenance_suppressed_until
            model.latest_note_at = state.latest_note_at
            model.latest_note_by = state.latest_note_by
            model.route_snapshot_json = state.route_snapshot_json
            model.incident_key = state.incident_key
        else:
            model = EscalationStateModel(
                state_id=state.state_id or str(uuid.uuid4()),
                source_event_id=state.source_event_id,
                source_history_id=state.source_history_id,
                source_event_type=state.source_event_type,
                seller_account_id=state.seller_account_id,
                environment_type=state.environment_type,
                sku=state.sku,
                dedupe_key=state.dedupe_key,
                current_status=state.current_status or "open",
                current_severity=state.current_severity,
                current_priority=state.current_priority,
                reminder_count=state.reminder_count or 0,
                escalation_level=state.escalation_level or 0,
                first_seen_at=state.first_seen_at or datetime.now(),
                last_seen_at=state.last_seen_at or datetime.now(),
                acked_at=state.acked_at,
                acked_by=state.acked_by,
                silenced_until=state.silenced_until,
                resolved_at=state.resolved_at,
                resolved_by=state.resolved_by,
                resolution_note=state.resolution_note,
                source_status_snapshot=state.source_status_snapshot,
                meta_json=state.meta_json,
                
                # v0.2 Extensions
                aging_seconds=state.aging_seconds,
                aging_bucket=state.aging_bucket,
                sla_target_seconds=state.sla_target_seconds,
                sla_breached_at=state.sla_breached_at,
                sla_breach_count=state.sla_breach_count,
                re_escalation_count=state.re_escalation_count,
                last_re_escalated_at=state.last_re_escalated_at,
                maintenance_suppressed_until=state.maintenance_suppressed_until,
                latest_note_at=state.latest_note_at,
                latest_note_by=state.latest_note_by,
                route_snapshot_json=state.route_snapshot_json,
                incident_key=state.incident_key,
                
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.session.add(model)
        
        self.session.commit()
        return self._to_domain_state(model)

    def get_by_state_id(self, state_id: str) -> Optional[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_state(model)

    def get_by_dedupe_key(self, dedupe_key: str) -> Optional[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.dedupe_key == dedupe_key)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_state(model)

    def list_unresolved_due_for_reminder(
        self,
        now: datetime,
        limit: Optional[int] = None,
        seller_account_id: Optional[str] = None,
        environment_type: Optional[str] = None
    ) -> List[EscalationState]:
        # Unresolved states: current_status in ('open', 'acknowledged', 'escalated')
        # Resolved is resolved_at IS NULL
        conditions = [
            EscalationStateModel.resolved_at.is_(None),
            EscalationStateModel.current_status != "resolved",
            or_(
                EscalationStateModel.silenced_until.is_(None),
                EscalationStateModel.silenced_until <= now
            )
        ]
        if seller_account_id:
            conditions.append(EscalationStateModel.seller_account_id == seller_account_id)
        if environment_type:
            conditions.append(EscalationStateModel.environment_type == environment_type)

        stmt = select(EscalationStateModel).where(and_(*conditions)).order_by(EscalationStateModel.updated_at.asc())
        if limit:
            stmt = stmt.limit(limit)

        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_unresolved_due_for_escalation(
        self,
        now: datetime,
        limit: Optional[int] = None,
        seller_account_id: Optional[str] = None,
        environment_type: Optional[str] = None
    ) -> List[EscalationState]:
        # Evaluated similarly to reminder lists
        return self.list_unresolved_due_for_reminder(now, limit, seller_account_id, environment_type)

    def mark_acknowledged(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        prev = model.current_status
        model.current_status = "acknowledged"
        model.acked_at = datetime.now()
        model.acked_by = actor_id
        model.updated_at = datetime.now()
        
        self.append_transition(
            state_id=state_id,
            action_type="acknowledge",
            previous_status=prev,
            new_status="acknowledged",
            actor_type="user",
            actor_id=actor_id,
            note=note
        )
        self.session.commit()
        return True

    def mark_silenced(self, state_id: str, silenced_until: datetime, actor_id: str, note: Optional[str] = None) -> bool:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        prev = model.current_status
        model.current_status = "silenced"
        model.silenced_until = silenced_until
        model.updated_at = datetime.now()

        self.append_transition(
            state_id=state_id,
            action_type="silence",
            previous_status=prev,
            new_status="silenced",
            actor_type="user",
            actor_id=actor_id,
            note=note,
            meta_json={"silenced_until": silenced_until.isoformat()}
        )
        self.session.commit()
        return True

    def clear_silence(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        prev = model.current_status
        model.current_status = "open"
        model.silenced_until = None
        model.updated_at = datetime.now()

        self.append_transition(
            state_id=state_id,
            action_type="unsilence",
            previous_status=prev,
            new_status="open",
            actor_type="user",
            actor_id=actor_id,
            note=note
        )
        self.session.commit()
        return True

    def mark_resolved(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        prev = model.current_status
        model.current_status = "resolved"
        model.resolved_at = datetime.now()
        model.resolved_by = actor_id
        model.resolution_note = note
        model.updated_at = datetime.now()

        self.append_transition(
            state_id=state_id,
            action_type="resolve",
            previous_status=prev,
            new_status="resolved",
            actor_type="user",
            actor_id=actor_id,
            note=note
        )
        self.session.commit()
        return True

    def reopen_state(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        prev = model.current_status
        model.current_status = "open"
        model.resolved_at = None
        model.resolved_by = None
        model.resolution_note = None
        model.reminder_count = 0
        model.escalation_level = 0
        
        # v0.2 Extensions reset
        model.aging_seconds = 0
        model.aging_bucket = None
        model.sla_breached_at = None
        model.sla_breach_count = 0
        model.re_escalation_count = 0
        model.last_re_escalated_at = None
        
        model.updated_at = datetime.now()

        self.append_transition(
            state_id=state_id,
            action_type="reopen",
            previous_status=prev,
            new_status="open",
            actor_type="user",
            actor_id=actor_id,
            note=note
        )
        self.session.commit()
        return True

    def append_transition(
        self,
        state_id: str,
        action_type: str,
        previous_status: Optional[str],
        new_status: str,
        actor_type: str,
        actor_id: Optional[str],
        note: Optional[str] = None,
        meta_json: Optional[Dict[str, Any]] = None
    ) -> EscalationStateTransition:
        model = EscalationStateTransitionModel(
            transition_id=str(uuid.uuid4()),
            state_id=state_id,
            action_type=action_type,
            previous_status=previous_status,
            new_status=new_status,
            actor_type=actor_type,
            actor_id=actor_id,
            note=note,
            meta_json=meta_json or {},
            created_at=datetime.now()
        )
        self.session.add(model)
        return EscalationStateTransition(
            transition_id=model.transition_id,
            state_id=model.state_id,
            action_type=model.action_type,
            previous_status=model.previous_status,
            new_status=model.new_status,
            actor_type=model.actor_type,
            actor_id=model.actor_id,
            note=model.note,
            meta_json=model.meta_json,
            created_at=model.created_at
        )

    def increment_reminder_count(self, state_id: str, new_count: int, last_notified_at: datetime) -> None:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            model.reminder_count = new_count
            model.last_reminded_at = last_notified_at
            model.last_notified_at = last_notified_at
            model.updated_at = datetime.now()
            self.session.commit()

    def set_escalation_level(self, state_id: str, new_level: int, last_escalated_at: datetime, target_severity: str, target_priority: str) -> None:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            model.escalation_level = new_level
            model.last_escalated_at = last_escalated_at
            model.last_notified_at = last_escalated_at
            model.current_severity = target_severity
            model.current_priority = target_priority
            model.current_status = "escalated"
            model.updated_at = datetime.now()
            
            self.append_transition(
                state_id=state_id,
                action_type="escalate",
                previous_status=model.current_status,
                new_status="escalated",
                actor_type="system",
                actor_id="escalation_engine",
                note=f"Escalated to Level {new_level} ({target_severity} - {target_priority})"
            )
            self.session.commit()

    def touch_last_seen(self, state_id: str) -> None:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            model.last_seen_at = datetime.now()
            model.updated_at = datetime.now()
            self.session.commit()

    def list_recent(self, limit: int = 20) -> List[EscalationState]:
        stmt = select(EscalationStateModel).order_by(EscalationStateModel.created_at.desc()).limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_by_status(self, status: str) -> List[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.current_status == status).order_by(EscalationStateModel.updated_at.desc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_by_event_type(self, event_type: str) -> List[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.source_event_type == event_type).order_by(EscalationStateModel.updated_at.desc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_by_sku(self, sku: str) -> List[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.sku == sku).order_by(EscalationStateModel.updated_at.desc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_stats(self) -> Dict[str, int]:
        stmt = select(EscalationStateModel.current_status, func.count(EscalationStateModel.state_id)).group_by(EscalationStateModel.current_status)
        results = self.session.execute(stmt).all()
        stats = {"open": 0, "acknowledged": 0, "silenced": 0, "escalated": 0, "resolved": 0}
        for status, count in results:
            if status in stats:
                stats[status] = count
        return stats

    def _to_domain_state(self, model: EscalationStateModel) -> EscalationState:
        return EscalationState(
            state_id=model.state_id,
            source_event_id=model.source_event_id,
            source_history_id=model.source_history_id,
            source_event_type=model.source_event_type,
            seller_account_id=model.seller_account_id,
            environment_type=model.environment_type,
            sku=model.sku,
            dedupe_key=model.dedupe_key,
            current_status=model.current_status,
            current_severity=model.current_severity,
            current_priority=model.current_priority,
            reminder_count=model.reminder_count,
            escalation_level=model.escalation_level,
            first_seen_at=model.first_seen_at,
            last_seen_at=model.last_seen_at,
            last_notified_at=model.last_notified_at,
            last_reminded_at=model.last_reminded_at,
            last_escalated_at=model.last_escalated_at,
            acked_at=model.acked_at,
            acked_by=model.acked_by,
            silenced_until=model.silenced_until,
            resolved_at=model.resolved_at,
            resolved_by=model.resolved_by,
            resolution_note=model.resolution_note,
            source_status_snapshot=model.source_status_snapshot or {},
            meta_json=model.meta_json or {},
            
            # v0.2 Extensions
            aging_seconds=model.aging_seconds,
            aging_bucket=model.aging_bucket,
            sla_target_seconds=model.sla_target_seconds,
            sla_breached_at=model.sla_breached_at,
            sla_breach_count=model.sla_breach_count,
            re_escalation_count=model.re_escalation_count,
            last_re_escalated_at=model.last_re_escalated_at,
            maintenance_suppressed_until=model.maintenance_suppressed_until,
            latest_note_at=model.latest_note_at,
            latest_note_by=model.latest_note_by,
            route_snapshot_json=model.route_snapshot_json or {},
            incident_key=model.incident_key,
            
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def list_breached(self, seller_account_id: Optional[str] = None, environment_type: Optional[str] = None) -> List[EscalationState]:
        conditions = [EscalationStateModel.sla_breached_at.is_not(None), EscalationStateModel.current_status != "resolved"]
        if seller_account_id:
            conditions.append(EscalationStateModel.seller_account_id == seller_account_id)
        if environment_type:
            conditions.append(EscalationStateModel.environment_type == environment_type)
        stmt = select(EscalationStateModel).where(and_(*conditions)).order_by(EscalationStateModel.sla_breached_at.asc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_by_aging_bucket(self, bucket: str, seller_account_id: Optional[str] = None, environment_type: Optional[str] = None) -> List[EscalationState]:
        conditions = [EscalationStateModel.aging_bucket == bucket, EscalationStateModel.current_status != "resolved"]
        if seller_account_id:
            conditions.append(EscalationStateModel.seller_account_id == seller_account_id)
        if environment_type:
            conditions.append(EscalationStateModel.environment_type == environment_type)
        stmt = select(EscalationStateModel).where(and_(*conditions)).order_by(EscalationStateModel.updated_at.asc())
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def increment_re_escalation_count(self, state_id: str, new_count: int, last_re_escalated_at: datetime) -> None:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            model.re_escalation_count = new_count
            model.last_re_escalated_at = last_re_escalated_at
            model.updated_at = datetime.now()
            self.session.commit()

    def mark_sla_breached(self, state_id: str, breached_at: datetime, target_severity: Optional[str], target_priority: Optional[str]) -> None:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id == state_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            if not model.sla_breached_at:
                model.sla_breached_at = breached_at
            model.sla_breach_count += 1
            if target_severity:
                model.current_severity = target_severity
            if target_priority:
                model.current_priority = target_priority
            model.updated_at = datetime.now()
            self.append_transition(
                state_id=state_id,
                action_type="sla_breach",
                previous_status=model.current_status,
                new_status=model.current_status,
                actor_type="system",
                actor_id="sla_engine",
                note=f"SLA Breached ({model.sla_breach_count} times)"
            )
            self.session.commit()

    def list_for_bulk_action(self, state_ids: List[str]) -> List[EscalationState]:
        stmt = select(EscalationStateModel).where(EscalationStateModel.state_id.in_(state_ids))
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_state(r) for r in results]

    def list_timeline_source_items(self, state_id: str) -> List[Dict[str, Any]]:
        # Returns transitions for the timeline
        stmt = select(EscalationStateTransitionModel).where(EscalationStateTransitionModel.state_id == state_id).order_by(EscalationStateTransitionModel.created_at.asc())
        results = self.session.execute(stmt).scalars().all()
        items = []
        for r in results:
            items.append({
                "type": "transition",
                "transition_id": r.transition_id,
                "action_type": r.action_type,
                "previous_status": r.previous_status,
                "new_status": r.new_status,
                "actor_type": r.actor_type,
                "actor_id": r.actor_id,
                "note": r.note,
                "meta_json": r.meta_json,
                "created_at": r.created_at
            })
        return items


class PersistentEscalationPolicyRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, policy: EscalationPolicy) -> EscalationPolicy:
        return self.upsert(policy)

    def upsert(self, policy: EscalationPolicy) -> EscalationPolicy:
        stmt = select(EscalationPolicyModel).where(EscalationPolicyModel.policy_id == policy.policy_id)
        model = self.session.execute(stmt).scalar_one_or_none()

        steps_json = [s.to_dict() for s in policy.escalation_steps]

        if model:
            model.name = policy.name
            model.enabled = policy.enabled
            model.seller_account_id = policy.seller_account_id
            model.environment_type = policy.environment_type
            model.event_type = policy.event_type
            model.base_severity = policy.base_severity
            model.reminder_enabled = policy.reminder_enabled
            model.reminder_interval_seconds = policy.reminder_interval_seconds
            model.reminder_max_count = policy.reminder_max_count
            model.allow_reminder_after_ack = policy.allow_reminder_after_ack
            model.silence_respected = policy.silence_respected
            model.auto_resolve_on_source_recovery = policy.auto_resolve_on_source_recovery
            model.escalation_enabled = policy.escalation_enabled
            model.escalation_steps_json = steps_json
            model.dedupe_scope = policy.dedupe_scope
            model.updated_at = datetime.now()
        else:
            model = EscalationPolicyModel(
                policy_id=policy.policy_id or str(uuid.uuid4()),
                name=policy.name,
                enabled=policy.enabled,
                seller_account_id=policy.seller_account_id,
                environment_type=policy.environment_type,
                event_type=policy.event_type,
                base_severity=policy.base_severity,
                reminder_enabled=policy.reminder_enabled,
                reminder_interval_seconds=policy.reminder_interval_seconds,
                reminder_max_count=policy.reminder_max_count,
                allow_reminder_after_ack=policy.allow_reminder_after_ack,
                silence_respected=policy.silence_respected,
                auto_resolve_on_source_recovery=policy.auto_resolve_on_source_recovery,
                escalation_enabled=policy.escalation_enabled,
                escalation_steps_json=steps_json,
                dedupe_scope=policy.dedupe_scope,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.session.add(model)
        
        self.session.commit()
        return self._to_domain_policy(model)

    def get_by_policy_id(self, policy_id: str) -> Optional[EscalationPolicy]:
        stmt = select(EscalationPolicyModel).where(EscalationPolicyModel.policy_id == policy_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_policy(model)

    def list_enabled(self) -> List[EscalationPolicy]:
        stmt = select(EscalationPolicyModel).where(EscalationPolicyModel.enabled == True)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_policy(r) for r in results]

    def list_for_event_type(self, event_type: str) -> List[EscalationPolicy]:
        stmt = select(EscalationPolicyModel).where(
            and_(
                EscalationPolicyModel.event_type == event_type,
                EscalationPolicyModel.enabled == True
            )
        )
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain_policy(r) for r in results]

    def resolve_best_policy(
        self,
        seller_account_id: Optional[str],
        environment_type: Optional[str],
        event_type: str,
        severity: str
    ) -> Optional[EscalationPolicy]:
        # Query all enabled policies matching the given event_type
        enabled_policies = self.list_for_event_type(event_type)
        if not enabled_policies:
            return None

        # 1. Exact Match: seller_account_id + environment_type + event_type
        for p in enabled_policies:
            if p.seller_account_id == seller_account_id and p.environment_type == environment_type:
                return p

        # 2. Match environment_type + event_type
        for p in enabled_policies:
            if p.environment_type == environment_type and not p.seller_account_id:
                return p

        # 3. Match seller_account_id + event_type
        for p in enabled_policies:
            if p.seller_account_id == seller_account_id and not p.environment_type:
                return p

        # 4. Fallback Match: event_type only
        for p in enabled_policies:
            if not p.seller_account_id and not p.environment_type:
                return p

        return None

    def _to_domain_policy(self, model: EscalationPolicyModel) -> EscalationPolicy:
        steps_raw = model.escalation_steps_json or []
        steps = [EscalationStep.from_dict(s) for s in steps_raw]
        return EscalationPolicy(
            policy_id=model.policy_id,
            name=model.name,
            enabled=model.enabled,
            seller_account_id=model.seller_account_id,
            environment_type=model.environment_type,
            event_type=model.event_type,
            base_severity=model.base_severity,
            reminder_enabled=model.reminder_enabled,
            reminder_interval_seconds=model.reminder_interval_seconds,
            reminder_max_count=model.reminder_max_count,
            allow_reminder_after_ack=model.allow_reminder_after_ack,
            silence_respected=model.silence_respected,
            auto_resolve_on_source_recovery=model.auto_resolve_on_source_recovery,
            escalation_enabled=model.escalation_enabled,
            escalation_steps=steps,
            dedupe_scope=model.dedupe_scope,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
