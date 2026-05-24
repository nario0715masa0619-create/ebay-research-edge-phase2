from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

class ExecutionState(str, Enum):
    ready_for_execution = "ready_for_execution"
    executing = "executing"
    executed = "executed"
    failed = "failed"
    rolled_back = "rolled_back"

@dataclass
class ExecutionTransition:
    from_state: ExecutionState
    to_state: ExecutionState
    reason: str
    timestamp: datetime
    initiated_by: Optional[str] = None

class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class ReadinessThresholdNotMetError(Exception):
    """Raised when readiness score is below the threshold for execution."""
    pass
