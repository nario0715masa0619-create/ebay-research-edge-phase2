from datetime import datetime, timedelta
from src.escalation.models import EscalationState, EscalationPolicy, ReminderExecutionResult

class ReminderDecisionEngine:
    def evaluate(self, state: EscalationState, policy: EscalationPolicy, now: datetime) -> ReminderExecutionResult:
        if not policy.reminder_enabled:
            return ReminderExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason="Reminder is disabled by policy."
            )

        if state.resolved_at is not None or state.current_status == "resolved":
            return ReminderExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason="Event is already resolved."
            )

        if policy.silence_respected and state.silenced_until is not None:
            if now < state.silenced_until:
                return ReminderExecutionResult(
                    state_id=state.state_id,
                    decision="silenced",
                    skipped_reason=f"Event is silenced until {state.silenced_until.isoformat()}."
                )

        if not policy.allow_reminder_after_ack and (state.acked_at is not None or state.current_status == "acknowledged"):
            return ReminderExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason="Event has been acknowledged and post-ack reminders are disallowed."
            )

        if policy.reminder_max_count is not None and state.reminder_count >= policy.reminder_max_count:
            return ReminderExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason=f"Reached maximum reminder limit of {policy.reminder_max_count}."
            )

        # Check interval
        base_time = state.last_notified_at or state.first_seen_at
        elapsed = (now - base_time).total_seconds()
        if elapsed < policy.reminder_interval_seconds:
            return ReminderExecutionResult(
                state_id=state.state_id,
                decision="skip",
                skipped_reason=f"Interval cooldown active. Only {elapsed:.1f}s elapsed of required {policy.reminder_interval_seconds}s."
            )

        # Due for reminder!
        next_due = now + timedelta(seconds=policy.reminder_interval_seconds)
        dispatched = ["slack"]
        if policy.escalation_steps:
            dispatched = policy.escalation_steps[0].target_channels

        return ReminderExecutionResult(
            state_id=state.state_id,
            decision="remind",
            dispatched_channels=dispatched,
            reminder_count_after=state.reminder_count + 1,
            next_due_at=next_due
        )
