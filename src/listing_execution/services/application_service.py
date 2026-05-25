from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.gateways.execution_gateway import ExecutionGateway
from src.listing_execution.services.execution_state_machine import ExecutionStateMachine, ReadinessThresholdNotMetError
from src.listing_execution.services.retry_manager import ExecutionRetryManager, RetryAction
from src.listing_readiness.services.readiness_checker import ReadinessChecker, ReadinessResult
from src.listing_execution.repositories.execution_attempt_repository import ExecutionAttemptRepository
from src.listing_execution.models.execution_state import ExecutionState
from src.listing_execution.executors.mock_executor import MockExecutor
from src.listing_execution.executors.live_executor import LiveExecutor
from src.listing_execution.gateways.ebay_api_gateway import EBayApiGateway
from src.listing_execution.services.listing_sync_service import ListingSyncService
from src.monitoring.services.execution_monitor import ExecutionMonitor

class ExecutionApplicationService:
    """
    Central orchestration service for the Execution Layer.
    Aggregates Readiness, State Machine, Gateway (Executor), Retry Policy, and Persistence.
    """
    def __init__(
        self,
        gateway: ExecutionGateway,
        readiness_checker: ReadinessChecker,
        repository: ExecutionAttemptRepository,
        retry_manager: Optional[ExecutionRetryManager] = None
    ):
        self.gateway = gateway
        self.readiness_checker = readiness_checker
        self.repository = repository
        self.retry_manager = retry_manager or ExecutionRetryManager()
        self.sync_service = ListingSyncService()
        self.monitor = ExecutionMonitor(repository=None)

    def check_readiness(self, candidate_data: Dict[str, Any], seller_data: Dict[str, Any], handoff_data: Dict[str, Any]) -> ReadinessResult:
        """Thin wrapper to execute readiness checklist."""
        return self.readiness_checker.check_readiness(candidate_data, seller_data, handoff_data)

    def execute_listing(
        self, 
        payload: ExecutionPayload, 
        candidate_data: Dict[str, Any], 
        seller_data: Dict[str, Any], 
        handoff_data: Dict[str, Any], 
        current_attempt_number: int = 1
    ) -> Dict[str, Any]:
        """
        Main entrypoint for executing a listing.
        1. Checks Readiness
        2. Initiates State Machine
        3. Validates and Executes via Gateway
        4. Evaluates Retries on Failure
        5. Persists Attempts
        """
        # Step 1: Readiness
        readiness_result = self.check_readiness(candidate_data, seller_data, handoff_data)
        
        state_machine = ExecutionStateMachine()
        
        try:
            # Step 2: Initiate State Machine (will raise error if readiness < 80)
            state_machine.initiate(readiness_result, initiated_by="system_execution")
            
            # Save Initial Attempt Record (if not dry_run)
            if not payload.dry_run:
                self.repository.create_attempt({
                    "attempt_id": payload.attempt_id,
                    "listing_id": payload.listing_id,
                    "candidate_id": candidate_data.get("candidate_id"),
                    "handoff_id": handoff_data.get("handoff_id"),
                    "seller_account_id": payload.seller,
                    "environment": payload.environment,
                    "status": ExecutionState.executing.value,
                    "payload_json": payload.to_dict(),
                    "retry_count": current_attempt_number - 1
                })

            # Step 3: Validate and Execute
            val_result = self.gateway.validate(payload)
            if not val_result.is_valid:
                # Handle Invalid seller/env guard failures early
                from src.listing_execution.gateways.execution_gateway import ExecutionResult
                mock_exec_result = ExecutionResult(
                    status="failed",
                    listing_id=payload.listing_id,
                    attempt_id=payload.attempt_id,
                    error_reason=", ".join(val_result.error_messages),
                    executed_at=datetime.now(timezone.utc)
                )
                state_machine.complete(mock_exec_result, initiated_by="system_execution")
                
                return self._handle_execution_failure(
                    payload, state_machine, ", ".join(val_result.error_messages), current_attempt_number, is_validation_failure=True
                )

            exec_result = self.gateway.execute(payload)
            
            # Step 4: Handle Execution Output
            state_machine.complete(exec_result, initiated_by="system_execution")
            
            if exec_result.status == "success":
                # Success Flow
                if not payload.dry_run:
                    self.repository.update_status(
                        attempt_id=payload.attempt_id,
                        status=ExecutionState.executed.value,
                        finished_at=datetime.now(timezone.utc)
                    )
                return {
                    "attempt_id": payload.attempt_id,
                    "status": "success",
                    "state": state_machine.current_state.value,
                    "dry_run": payload.dry_run,
                    "listing_id": payload.listing_id
                }
            else:
                # Execution Failed Flow
                return self._handle_execution_failure(
                    payload, state_machine, exec_result.error_reason, current_attempt_number
                )

        except ReadinessThresholdNotMetError as e:
            # Reject execution safely
            return {
                "attempt_id": payload.attempt_id,
                "status": "rejected",
                "state": ExecutionState.ready_for_execution.value,
                "error_reason": str(e),
                "dry_run": payload.dry_run
            }
        except Exception as e:
            # Unknown exceptions
            return self._handle_execution_failure(
                payload, state_machine, str(e), current_attempt_number
            )

    def execute_with_live_gateway(
        self,
        payload: ExecutionPayload,
        credentials: Optional[Dict[str, str]],
        candidate_data: Dict[str, Any],
        seller_data: Dict[str, Any],
        handoff_data: Dict[str, Any],
        current_attempt_number: int = 1
    ) -> Dict[str, Any]:
        """
        End-to-end execution flow with Live/Mock selection based on dry_run and credentials.
        Also integrates ListingSyncService and ExecutionMonitor.
        """
        # Step 1: Readiness
        readiness_result = self.check_readiness(candidate_data, seller_data, handoff_data)
        
        if self.repository:
            self.repository.append_history_event(
                attempt_id=payload.attempt_id,
                event_type="readiness_passed" if readiness_result.readiness_score >= 80 else "readiness_failed",
                dry_run=payload.dry_run,
                details={"score": readiness_result.readiness_score, "reasons": readiness_result.readiness_reasons}
            )

        state_machine = ExecutionStateMachine(
            attempt_id=payload.attempt_id,
            repository=self.repository,
            dry_run=payload.dry_run
        )

        try:
            state_machine.initiate(readiness_result, initiated_by="system_execution")

            if not payload.dry_run:
                self.repository.create_attempt({
                    "attempt_id": payload.attempt_id,
                    "listing_id": payload.listing_id,
                    "candidate_id": candidate_data.get("candidate_id"),
                    "handoff_id": handoff_data.get("handoff_id"),
                    "seller_account_id": payload.seller,
                    "environment": payload.environment,
                    "status": ExecutionState.executing.value,
                    "payload_json": payload.to_dict(),
                    "retry_count": current_attempt_number - 1
                })

            # Select Executor
            if payload.dry_run:
                executor = MockExecutor(
                    allowed_environments=[payload.environment],
                    allowed_sellers=[payload.seller],
                    fixture_rules={}
                )
                if self.repository:
                    self.repository.append_history_event(payload.attempt_id, "executor_selection", payload.dry_run, details={"mode": "mock"})
                    self.repository.append_history_event(payload.attempt_id, "dry_run_executed", payload.dry_run)
            elif not credentials:
                # Invalid credentials -> reject
                from src.listing_execution.gateways.execution_gateway import ExecutionResult
                res = ExecutionResult(
                    status="failed",
                    listing_id=payload.listing_id,
                    attempt_id=payload.attempt_id,
                    error_reason="Missing credentials for live execution",
                    executed_at=datetime.now(timezone.utc)
                )
                state_machine.complete(res, initiated_by="system_execution")
                return self._handle_e2e_failure(payload, state_machine, res, current_attempt_number, is_validation_failure=True)
            else:
                executor = LiveExecutor(
                    api_gateway=EBayApiGateway(credentials),
                    allowed_environments=[payload.environment],
                    allowed_sellers=[payload.seller]
                )
                if self.repository:
                    self.repository.append_history_event(payload.attempt_id, "executor_selection", payload.dry_run, details={"mode": "live"})

            # Validate and Execute
            val_result = executor.validate(payload, credentials)
            if not val_result.is_valid:
                if self.repository:
                    self.repository.append_history_event(
                        payload.attempt_id, "guard_rejected", payload.dry_run, 
                        error_message=", ".join(val_result.error_messages)
                    )
                from src.listing_execution.gateways.execution_gateway import ExecutionResult
                res = ExecutionResult(
                    status="failed",
                    listing_id=payload.listing_id,
                    attempt_id=payload.attempt_id,
                    error_reason=", ".join(val_result.error_messages),
                    executed_at=datetime.now(timezone.utc)
                )
                state_machine.complete(res, initiated_by="system_execution")
                return self._handle_e2e_failure(payload, state_machine, res, current_attempt_number, is_validation_failure=True)

            if self.repository:
                self.repository.append_history_event(payload.attempt_id, "gateway_validated", payload.dry_run)

            exec_result = executor.execute(payload, credentials)
            state_machine.complete(exec_result, initiated_by="system_execution")

            # Monitoring
            if exec_result.status == "failed":
                return self._handle_e2e_failure(payload, state_machine, exec_result, current_attempt_number)

            # Success -> Sync
            try:
                self.sync_service.sync_execution_to_listing(exec_result, payload.listing_id, payload.dry_run)
                if self.repository:
                    self.repository.append_history_event(
                        payload.attempt_id, "listing_state_changed", payload.dry_run,
                        details={"synced": True}
                    )
            except Exception as e:
                # Conflict or sync error
                exec_result.status = "failed"
                exec_result.error_reason = str(e)
                self.sync_service.handle_rollback(exec_result.attempt_id, exec_result.listing_id, payload.dry_run)
                return self._handle_e2e_failure(payload, state_machine, exec_result, current_attempt_number)

            if not payload.dry_run:
                self.repository.update_status(
                    attempt_id=payload.attempt_id,
                    status=ExecutionState.executed.value,
                    finished_at=datetime.now(timezone.utc)
                )

            return {
                "attempt_id": payload.attempt_id,
                "status": "success",
                "state": state_machine.current_state.value,
                "dry_run": payload.dry_run,
                "listing_id": payload.listing_id
            }

        except ReadinessThresholdNotMetError as e:
            return {
                "attempt_id": payload.attempt_id,
                "status": "rejected",
                "state": ExecutionState.ready_for_execution.value,
                "error_reason": str(e),
                "dry_run": payload.dry_run
            }
        except Exception as e:
            from src.listing_execution.gateways.execution_gateway import ExecutionResult
            res = ExecutionResult(status="failed", listing_id=payload.listing_id, attempt_id=payload.attempt_id, error_reason=str(e), executed_at=datetime.now(timezone.utc))
            if state_machine.current_state == ExecutionState.executing:
                state_machine.complete(res, initiated_by="system_execution")
            return self._handle_e2e_failure(payload, state_machine, res, current_attempt_number)

    def _handle_e2e_failure(self, payload, state_machine, exec_result, current_attempt_number, is_validation_failure=False):
        # Sync Service failure handling
        try:
            self.sync_service.handle_execution_failure(exec_result, exec_result.listing_id, payload.dry_run)
        except Exception:
            pass
            
        failure_response = self._handle_execution_failure(payload, state_machine, exec_result.error_reason, current_attempt_number, is_validation_failure)
        
        # Monitoring integration
        attempt_history = {
            "failure_boundary": failure_response.get("failure_boundary", "UNKNOWN"),
            "retry_count": current_attempt_number - 1,
            "max_attempts": 3,
            "next_retry_at": failure_response.get("next_retry_at"),
            "is_cancelled": failure_response.get("action") == RetryAction.CANCEL.value
        }
        
        alert = self.monitor.process_execution_result(exec_result, payload.listing_id, attempt_history, dry_run=payload.dry_run)
        
        if self.repository and alert:
            self.repository.append_history_event(
                payload.attempt_id, "alert_created", payload.dry_run,
                details={"alert_level": alert.alert_level.value if hasattr(alert.alert_level, "value") else str(alert.alert_level)}
            )
        
        return failure_response

    def _handle_execution_failure(
        self, 
        payload: ExecutionPayload, 
        state_machine: ExecutionStateMachine, 
        error_reason: str, 
        current_attempt_number: int,
        is_validation_failure: bool = False
    ) -> Dict[str, Any]:
        """
        Internal handler for execution failures.
        Delegates to RetryManager and decides next steps.
        """
        if is_validation_failure:
            # Validation failures (guards) are non-retryable and cancel immediately
            action, reason = RetryAction.CANCEL, "Validation Failed (Guard blocked)"
            next_attempt_number = None
            next_retry_at = None
            failure_boundary = "VALIDATION_GUARD"
        else:
            decision = self.retry_manager.evaluate_failure(error_reason, attempt_number=current_attempt_number)
            action = decision.action
            reason = decision.reason
            next_attempt_number = decision.next_attempt_number
            next_retry_at = decision.next_retry_at
            failure_boundary = self.retry_manager.classify_failure(error_reason).value

        # Rollback execution scope if it's retryable or cancelled
        self.retry_manager.safely_rollback_execution_scope(state_machine, payload.attempt_id, reason)
        
        if self.repository:
            if action == RetryAction.RETRY_LATER:
                self.repository.append_history_event(
                    payload.attempt_id, "retry_scheduled", payload.dry_run,
                    details={"next_attempt": next_attempt_number, "retry_at": next_retry_at.isoformat() if next_retry_at else None}
                )
            else:
                self.repository.append_history_event(
                    payload.attempt_id, "retry_cancelled", payload.dry_run,
                    details={"reason": reason}
                )

        if not payload.dry_run:
            self.repository.update_status(
                attempt_id=payload.attempt_id,
                status=ExecutionState.failed.value if action == RetryAction.CANCEL else state_machine.current_state.value,
                error_message=error_reason,
                error_code=action.value,
                failure_boundary=failure_boundary,
                finished_at=datetime.now(timezone.utc)
            )

        return {
            "attempt_id": payload.attempt_id,
            "status": "failed",
            "state": state_machine.current_state.value,
            "action": action.value,
            "error_reason": error_reason,
            "retry_decision": reason,
            "next_attempt_number": next_attempt_number,
            "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
            "dry_run": payload.dry_run,
            "failure_boundary": failure_boundary
        }

    def get_attempt_status(self, attempt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve attempt info"""
        attempt = self.repository.get_by_id(attempt_id)
        if not attempt:
            return None
        return {
            "attempt_id": attempt.attempt_id,
            "status": attempt.status,
            "listing_id": attempt.listing_id,
            "error_message": attempt.error_message
        }

    def retry_execution(self, attempt_id: str, new_payload: ExecutionPayload, next_attempt_number: int) -> Dict[str, Any]:
        """Trigger a retry by executing with the newly provisioned payload (new attempt_id)."""
        return self.execute_listing(new_payload, current_attempt_number=next_attempt_number)

    def rollback_execution(self, attempt_id: str, reason: str) -> Dict[str, Any]:
        """Manual trigger to rollback an execution attempt scope."""
        state_machine = ExecutionStateMachine()
        # In a real system, we might load state_machine history from DB here.
        # For simplicity, we just transition to rolled_back.
        state_machine._current_state = ExecutionState.executed # Simulate it was executed
        
        self.retry_manager.safely_rollback_execution_scope(state_machine, attempt_id, reason)
        
        attempt = self.repository.update_status(
            attempt_id=attempt_id,
            status=ExecutionState.rolled_back.value,
            error_message=f"Manual Rollback: {reason}",
            finished_at=datetime.now(timezone.utc)
        )
        
        return {
            "attempt_id": attempt_id,
            "status": ExecutionState.rolled_back.value if attempt else "not_found"
        }
