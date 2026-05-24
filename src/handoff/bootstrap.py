from sqlalchemy.orm import Session
from typing import Tuple

from src.handoff.config import HandoffSettings
from src.handoff.handoff_service import HandoffService
from src.handoff.live_execution_dispatch_gateway import LiveExecutionDispatchGateway
from src.handoff.mock_execution_dispatch_gateway import MockExecutionDispatchGateway
from src.repositories.persistent_handoff_repository import PersistentHandoffRepository

def bootstrap_handoff_layer(session: Session) -> Tuple[HandoffService, PersistentHandoffRepository]:
    """
    Bootstraps the handoff layer, providing the configured service and repository.
    """
    settings = HandoffSettings()
    
    if settings.use_mock_gateway:
        gateway = MockExecutionDispatchGateway()
    else:
        # In the future, this might require injecting specific HTTP clients or API adapters
        gateway = LiveExecutionDispatchGateway()
        
    service = HandoffService(settings, gateway=gateway)
    repository = PersistentHandoffRepository(session)
    
    return service, repository
