from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ValidationResult:
    """
    Result of the pre-execution validation step.
    """
    is_valid: bool
    error_messages: List[str]

@dataclass
class ExecutionResult:
    """
    Result of the execution attempt.
    Status can be: success, timeout, seller_limit, state_conflict, error
    """
    status: str
    listing_id: str
    attempt_id: str
    executed_at: datetime
    error_reason: Optional[str] = None
