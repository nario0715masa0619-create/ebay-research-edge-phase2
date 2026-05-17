from datetime import datetime
from typing import List, Dict, Any, Optional
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository

class BulkActionService:
    def __init__(self, repository: PersistentEscalationStateRepository):
        self.repository = repository

    def bulk_ack(self, state_ids: List[str], actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success_count = 0
        failed_ids = []
        for state_id in state_ids:
            if self.repository.mark_acknowledged(state_id, actor_id, note):
                success_count += 1
            else:
                failed_ids.append(state_id)
        return {"success_count": success_count, "failed_ids": failed_ids}

    def bulk_resolve(self, state_ids: List[str], actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success_count = 0
        failed_ids = []
        for state_id in state_ids:
            if self.repository.mark_resolved(state_id, actor_id, note):
                success_count += 1
            else:
                failed_ids.append(state_id)
        return {"success_count": success_count, "failed_ids": failed_ids}

    def bulk_silence(self, state_ids: List[str], silenced_until: datetime, actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success_count = 0
        failed_ids = []
        for state_id in state_ids:
            if self.repository.mark_silenced(state_id, silenced_until, actor_id, note):
                success_count += 1
            else:
                failed_ids.append(state_id)
        return {"success_count": success_count, "failed_ids": failed_ids}

    def bulk_reopen(self, state_ids: List[str], actor_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        success_count = 0
        failed_ids = []
        for state_id in state_ids:
            if self.repository.reopen_state(state_id, actor_id, note):
                success_count += 1
            else:
                failed_ids.append(state_id)
        return {"success_count": success_count, "failed_ids": failed_ids}
