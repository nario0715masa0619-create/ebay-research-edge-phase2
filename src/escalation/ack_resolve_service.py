import logging
from datetime import datetime
from typing import Optional
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository

logger = logging.getLogger(__name__)

class AckResolveService:
    def __init__(self, state_repo: PersistentEscalationStateRepository):
        self.state_repo = state_repo

    def acknowledge(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        logger.info(f"Acknowledging escalation state {state_id} by actor {actor_id}")
        return self.state_repo.mark_acknowledged(state_id, actor_id, note)

    def silence(self, state_id: str, silenced_until: datetime, actor_id: str, note: Optional[str] = None) -> bool:
        logger.info(f"Silencing escalation state {state_id} until {silenced_until.isoformat()} by actor {actor_id}")
        return self.state_repo.mark_silenced(state_id, silenced_until, actor_id, note)

    def unsilence(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        logger.info(f"Unsilencing escalation state {state_id} by actor {actor_id}")
        return self.state_repo.clear_silence(state_id, actor_id, note)

    def resolve(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        logger.info(f"Resolving escalation state {state_id} by actor {actor_id}")
        return self.state_repo.mark_resolved(state_id, actor_id, note)

    def reopen(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        logger.info(f"Reopening escalation state {state_id} by actor {actor_id}")
        return self.state_repo.reopen_state(state_id, actor_id, note)
