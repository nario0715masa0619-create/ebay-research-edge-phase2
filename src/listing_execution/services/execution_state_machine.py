from typing import List, Optional
from datetime import datetime, timezone
from src.listing_execution.models.execution_state import (
    ExecutionState, 
    ExecutionTransition, 
    InvalidStateTransitionError,
    ReadinessThresholdNotMetError
)
from src.listing_readiness.services.readiness_checker import ReadinessResult
from src.listing_execution.models.results import ExecutionResult
from src.listing_execution.repositories.execution_attempt_repository import ExecutionAttemptRepository

class ExecutionStateMachine:
    def __init__(self, attempt_id: Optional[str] = None, repository: Optional[ExecutionAttemptRepository] = None, dry_run: bool = False):
        self._current_state = ExecutionState.ready_for_execution
        self._transitions: List[ExecutionTransition] = []
        self._attempt_id = attempt_id
        self._repository = repository
        self._dry_run = dry_run

    @property
    def current_state(self) -> ExecutionState:
        return self._current_state

    def validate_transition(self, from_state: ExecutionState, to_state: ExecutionState) -> bool:
        """
        Validates whether the state transition is allowed.
        """
        valid_transitions = {
            ExecutionState.ready_for_execution: [ExecutionState.executing],
            ExecutionState.executing: [ExecutionState.executed, ExecutionState.failed],
            ExecutionState.executed: [ExecutionState.rolled_back],
            ExecutionState.failed: [ExecutionState.rolled_back],
            ExecutionState.rolled_back: []
        }
        
        allowed_targets = valid_transitions.get(from_state, [])
        return to_state in allowed_targets

    def _apply_transition(self, to_state: ExecutionState, reason: str, initiated_by: str = None):
        if not self.validate_transition(self._current_state, to_state):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self._current_state.value} to {to_state.value}"
            )

        transition = ExecutionTransition(
            from_state=self._current_state,
            to_state=to_state,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
            initiated_by=initiated_by
        )
        self._transitions.append(transition)
        
        from_state_val = self._current_state.value
        to_state_val = to_state.value
        self._current_state = to_state

        if self._repository and self._attempt_id:
            event_type_map = {
                "executing": "execution_started",
                "executed": "execution_succeeded",
                "failed": "execution_failed",
                "rolled_back": "rollback_executed"
            }
            event_type = event_type_map.get(to_state_val, "unknown_state_change")
            self._repository.append_history_event(
                attempt_id=self._attempt_id,
                event_type=event_type,
                dry_run=self._dry_run,
                from_state=from_state_val,
                to_state=to_state_val,
                details={"reason": reason, "initiated_by": initiated_by}
            )

    def initiate(self, readiness_result: ReadinessResult, initiated_by: str = "system") -> ExecutionState:
        """
        readiness_result.score >= 80 の場合のみ ready_for_execution -> executing へ遷移
        """
        if readiness_result.readiness_score < 80:
            raise ReadinessThresholdNotMetError(
                f"Readiness score {readiness_result.readiness_score} does not meet threshold (80). "
                f"Reasons: {readiness_result.readiness_reasons}"
            )
            
        self._apply_transition(
            ExecutionState.executing, 
            f"Readiness check passed (score={readiness_result.readiness_score})",
            initiated_by
        )
        return self._current_state

    def complete(self, execution_result: ExecutionResult, initiated_by: str = "system") -> ExecutionState:
        """
        execution_result.status に応じて executed または failed に遷移
        """
        if execution_result.status == "success":
            to_state = ExecutionState.executed
            reason = f"Execution succeeded for listing {execution_result.listing_id}"
        else:
            to_state = ExecutionState.failed
            reason = f"Execution failed ({execution_result.status}): {execution_result.error_reason}"
            
        self._apply_transition(to_state, reason, initiated_by)
        return self._current_state

    def rollback(self, reason: str, initiated_by: str = "system") -> ExecutionState:
        """
        executing / executed / failed から rolled_back に遷移
        """
        # executing から rolled_back への直接遷移はルールに無いが、
        # 仕様として failed 経由または、設計通りの executed/failed からの遷移とする。
        # 遷移図上は executed -> rolled_back, failed -> rolled_back となっている。
        self._apply_transition(ExecutionState.rolled_back, f"Rollback requested: {reason}", initiated_by)
        return self._current_state

    def get_transition_history(self) -> List[ExecutionTransition]:
        """
        監査用の全遷移履歴を返す
        """
        return list(self._transitions)
