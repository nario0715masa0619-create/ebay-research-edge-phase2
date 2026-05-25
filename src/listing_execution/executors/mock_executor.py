from typing import Dict, List, Any
from datetime import datetime, timezone
from src.listing_execution.gateways.execution_gateway import ExecutionGateway
from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.models.results import ValidationResult, ExecutionResult

class MockExecutor(ExecutionGateway):
    """
    Mock implementation of ExecutionGateway for testing and dry-runs.
    Uses fixture rules mapped by SKU to determine execution outcome.
    """
    
    def __init__(self, allowed_environments: List[str], allowed_sellers: List[str], fixture_rules: Dict[str, str]):
        self.allowed_environments = allowed_environments
        self.allowed_sellers = allowed_sellers
        self.fixture_rules = fixture_rules
        
        # In-memory cache to simulate idempotency: {attempt_id: ExecutionResult}
        self._attempt_history: Dict[str, ExecutionResult] = {}
        # Simulate execution attempt records (for DB tracking placeholder)
        self.execution_attempt_records: List[Dict[str, Any]] = []

    def supports_environment(self, env: str) -> bool:
        return env in self.allowed_environments

    def validate(self, payload: ExecutionPayload, credentials: Dict[str, Any] = None) -> ValidationResult:
        errors = []
        if not self.supports_environment(payload.environment):
            errors.append(f"Environment '{payload.environment}' is not supported.")
            
        if payload.seller not in self.allowed_sellers:
            errors.append(f"Seller '{payload.seller}' is not authorized.")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_messages=errors
        )

    def execute(self, payload: ExecutionPayload, credentials: Dict[str, Any] = None) -> ExecutionResult:
        # Mandatory Guard Check
        val_result = self.validate(payload, credentials)
        if not val_result.is_valid:
            return ExecutionResult(
                status="error",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                executed_at=datetime.now(timezone.utc),
                error_reason="Validation Failed: " + ", ".join(val_result.error_messages)
            )

        # Idempotency Check
        if payload.attempt_id in self._attempt_history:
            return self._attempt_history[payload.attempt_id]

        # Dry Run Check
        if payload.dry_run:
            result = ExecutionResult(
                status="success",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                executed_at=datetime.now(timezone.utc),
                error_reason="Simulated (dry_run=True)"
            )
            # Record attempt but do not mutate external state
            self._record_attempt(payload, result)
            self._attempt_history[payload.attempt_id] = result
            return result

        # Mock Fixture Evaluation
        # If sku not in rules, default to success
        behavior = self.fixture_rules.get(payload.sku, "success")
        
        status = "success"
        error_reason = None
        
        if behavior == "timeout":
            status = "timeout"
            error_reason = "Mock API Timeout after 30s"
        elif behavior == "seller_limit":
            status = "seller_limit"
            error_reason = "eBay API Error 120: Seller exceeded limits"
        elif behavior == "state_conflict":
            status = "state_conflict"
            error_reason = "eBay API Error 21919301: Duplicate listing or invalid state"
        elif behavior == "error":
            status = "error"
            error_reason = "Unknown internal server error 500"

        result = ExecutionResult(
            status=status,
            listing_id=payload.listing_id,
            attempt_id=payload.attempt_id,
            executed_at=datetime.now(timezone.utc),
            error_reason=error_reason
        )

        self._record_attempt(payload, result)
        self._attempt_history[payload.attempt_id] = result
        return result

    def _record_attempt(self, payload: ExecutionPayload, result: ExecutionResult):
        """Simulate saving an execution_attempt record in memory"""
        self.execution_attempt_records.append({
            "attempt_id": payload.attempt_id,
            "listing_id": payload.listing_id,
            "status": result.status,
            "error_reason": result.error_reason,
            "executed_at": result.executed_at,
            "is_dry_run": payload.dry_run
        })
