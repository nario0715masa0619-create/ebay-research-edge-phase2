from abc import ABC, abstractmethod
from typing import Tuple, Optional
from src.handoff.models import HandoffInput

class ExecutionDispatchGateway(ABC):
    @abstractmethod
    def dispatch(self, handoff_id: str, input_data: HandoffInput, payload_ref: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Dispatches the handoff to the execution layer.
        
        Returns:
            Tuple[success, error_code, error_summary]
        """
        pass
