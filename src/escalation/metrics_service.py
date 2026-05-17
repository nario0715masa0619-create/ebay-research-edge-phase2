from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from src.db.models import EscalationStateModel
from src.escalation.models import EscalationStatsSnapshot

class MetricsService:
    def __init__(self, session: Session):
        self.session = session

    def get_snapshot(self) -> EscalationStatsSnapshot:
        # Core unresolved count
        unresolved_stmt = select(func.count(EscalationStateModel.state_id)).where(EscalationStateModel.current_status != "resolved")
        unresolved_total = self.session.execute(unresolved_stmt).scalar() or 0

        # Breached count
        breached_stmt = select(func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.sla_breached_at.is_not(None),
            EscalationStateModel.current_status != "resolved"
        )
        breached_total = self.session.execute(breached_stmt).scalar() or 0

        # Re-escalated total
        re_esc_stmt = select(func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.re_escalation_count > 0,
            EscalationStateModel.current_status != "resolved"
        )
        re_escalation_total = self.session.execute(re_esc_stmt).scalar() or 0

        # Aging Buckets
        aging_stmt = select(EscalationStateModel.aging_bucket, func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.current_status != "resolved"
        ).group_by(EscalationStateModel.aging_bucket)
        
        aging_bucket_counts = {}
        for bucket, count in self.session.execute(aging_stmt).all():
            bucket_key = bucket or "unknown"
            aging_bucket_counts[bucket_key] = count

        # Seller counts
        seller_stmt = select(EscalationStateModel.seller_account_id, func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.current_status != "resolved"
        ).group_by(EscalationStateModel.seller_account_id)
        
        seller_counts = {}
        for s_id, count in self.session.execute(seller_stmt).all():
            seller_key = s_id or "system"
            seller_counts[seller_key] = count

        # Environment counts
        env_stmt = select(EscalationStateModel.environment_type, func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.current_status != "resolved"
        ).group_by(EscalationStateModel.environment_type)
        
        env_counts = {}
        for env, count in self.session.execute(env_stmt).all():
            env_key = env or "system"
            env_counts[env_key] = count

        # Event type counts
        evt_stmt = select(EscalationStateModel.source_event_type, func.count(EscalationStateModel.state_id)).where(
            EscalationStateModel.current_status != "resolved"
        ).group_by(EscalationStateModel.source_event_type)
        
        evt_counts = {}
        for evt, count in self.session.execute(evt_stmt).all():
            evt_counts[evt] = count

        # Time to Ack (Approx avg)
        # Note: SQLite time operations are tricky with func.avg, simplified logic:
        # Calculate in Python for smaller datasets or leave as 0 for now.
        # Implementing a simple version using python.
        t_ack_stmt = select(EscalationStateModel.first_seen_at, EscalationStateModel.acked_at).where(
            EscalationStateModel.acked_at.is_not(None)
        ).order_by(EscalationStateModel.acked_at.desc()).limit(1000)
        
        t_acks = self.session.execute(t_ack_stmt).all()
        avg_ack = 0.0
        if t_acks:
            total = sum([(a - f).total_seconds() for f, a in t_acks if a and f])
            avg_ack = total / len(t_acks)
            
        t_res_stmt = select(EscalationStateModel.first_seen_at, EscalationStateModel.resolved_at).where(
            EscalationStateModel.resolved_at.is_not(None)
        ).order_by(EscalationStateModel.resolved_at.desc()).limit(1000)
        
        t_res = self.session.execute(t_res_stmt).all()
        avg_res = 0.0
        if t_res:
            total = sum([(r - f).total_seconds() for f, r in t_res if r and f])
            avg_res = total / len(t_res)

        return EscalationStatsSnapshot(
            unresolved_total=unresolved_total,
            breached_total=breached_total,
            re_escalation_total=re_escalation_total,
            aging_bucket_counts=aging_bucket_counts,
            seller_counts=seller_counts,
            environment_counts=env_counts,
            event_type_counts=evt_counts,
            avg_time_to_ack_seconds=avg_ack,
            avg_time_to_resolve_seconds=avg_res
        )
