from typing import Tuple, Optional
from src.handoff.execution_dispatch_gateway import ExecutionDispatchGateway
from src.handoff.models import HandoffInput

class MockExecutionDispatchGateway(ExecutionDispatchGateway):
    def dispatch(self, handoff_id: str, input_data: HandoffInput, payload_ref: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Mock implementation.
        Simulates success mostly, but can simulate failures based on candidate_id patterns for testing.
        """
        candidate_id = input_data.candidate_id.lower()
        
        # Simulate transient error
        if "mock_transient_error" in candidate_id:
            return False, "503_SERVICE_UNAVAILABLE", "Downstream readiness service is temporarily unavailable."
            
        # Simulate rate limit
        if "mock_rate_limit" in candidate_id:
            return False, "429_TOO_MANY_REQUESTS", "Rate limit exceeded on execution layer."
            
        # Simulate non-retryable error
        if "mock_fatal_error" in candidate_id:
            return False, "400_BAD_REQUEST", "Invalid payload format rejected by readiness layer."
            
        # Default success
        return True, "", ""
