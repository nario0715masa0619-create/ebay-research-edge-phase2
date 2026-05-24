from abc import ABC, abstractmethod
from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.models.results import ValidationResult, ExecutionResult

class ExecutionGateway(ABC):
    """
    Abstract base class defining the contract for executing listing payloads.
    Concrete implementations could be Live, Mock, or Staging.
    """
    
    @abstractmethod
    def execute(self, payload: ExecutionPayload) -> ExecutionResult:
        """
        Executes the payload on the target platform.
        """
        pass
        
    @abstractmethod
    def validate(self, payload: ExecutionPayload) -> ValidationResult:
        """
        Validates the payload against gateway-specific constraints (e.g. seller authorization, environment support).
        """
        pass
        
    @abstractmethod
    def supports_environment(self, env: str) -> bool:
        """
        Returns True if this gateway supports the given environment (e.g., 'production', 'sandbox').
        """
        pass
