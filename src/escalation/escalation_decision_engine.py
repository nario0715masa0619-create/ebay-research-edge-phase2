from datetime import datetime, timedelta
from src.escalation.models import EscalationState, EscalationPolicy, EscalationExecutionResult, EscalationStep

class EscalationDecisionEngine:
    def evaluate(self, state: EscalationState, policy: EscalationPolicy, now: datetime) -> EscalationExecutionResult:
        if not policy.escalation_enabled:
            return EscalationExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason="Escalation is disabled by policy."
            )

        if state.resolved_at is not None or state.current_status == "resolved":
            return EscalationExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason="Event is already resolved."
            )

        if policy.silence_respected and state.silenced_until is not None:
            if now < state.silenced_until:
                return EscalationExecutionResult(
                    state_id=state.state_id,
                    decision="skip",
                    skipped_reason="Event is silenced."
                )

        # Evaluate steps in descending order (highest step first)
        sorted_steps = sorted(policy.escalation_steps, key=lambda s: s.step_index, reverse=True)
        
        for step in sorted_steps:
            # Check if this step has already been reached
            if state.escalation_level >= step.step_index:
                continue

            # Check open duration (seconds since first_seen_at)
            open_seconds = (now - state.first_seen_at).total_seconds()
            if open_seconds < step.after_seconds:
                continue

            # Check repeat count / reminder count
            if state.reminder_count < step.min_repeat_count:
                continue

            # Check require_unacked
            if step.require_unacked and (state.acked_at is not None or state.current_status == "acknowledged"):
                continue

            # Check cooldown since last escalation
            if state.last_escalated_at is not None and step.cooldown_seconds > 0:
                elapsed_cooldown = (now - state.last_escalated_at).total_seconds()
                if elapsed_cooldown < step.cooldown_seconds:
                    continue

            # Eligible! Trigger escalation!
            return EscalationExecutionResult(
                state_id=state.state_id,
                decision="escalate",
                escalation_level_after=step.step_index,
                dispatched_channels=step.target_channels,
                next_due_at=now + timedelta(seconds=step.cooldown_seconds or 300)
            )

        return EscalationExecutionResult(
            state_id=state.state_id,
            decision="skip",
            skipped_reason="No escalation steps matched or due."
        )
