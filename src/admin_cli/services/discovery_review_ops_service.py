from typing import List, Optional, Dict, Any
from src.discovery.review_models import ReviewQueueItem, CandidateCompareView
from src.discovery.review_queue_service import ReviewQueueService
from src.discovery.review_decision_service import ReviewDecisionService
from src.repositories.persistent_alias_dictionary_repository import PersistentAliasDictionaryRepository, AliasRecord
import uuid

class DiscoveryReviewOpsService:
    """
    Facade service for Admin CLI and Web Interface to interact with Discovery Review capabilities.
    Enforces authorization/actor logging and aggregates necessary data.
    """
    
    def __init__(self, 
                 queue_service: ReviewQueueService, 
                 decision_service: ReviewDecisionService,
                 alias_repo: PersistentAliasDictionaryRepository):
        self.queue_service = queue_service
        self.decision_service = decision_service
        self.alias_repo = alias_repo

    # --- Queue & View Operations ---

    def list_pending_reviews(self, limit: int = 50, offset: int = 0) -> List[ReviewQueueItem]:
        return self.queue_service.get_pending_queue(limit=limit, offset=offset)

    def get_review_detail(self, candidate_id: str) -> Optional[CandidateCompareView]:
        return self.queue_service.get_candidate_compare_view(candidate_id)
        
    # --- Decision Operations ---

    def approve_candidate(self, candidate_id: str, actor: str, note: Optional[str] = None):
        return self.decision_service.approve(candidate_id, actor, note)

    def reject_candidate(self, candidate_id: str, actor: str, note: Optional[str] = None):
        return self.decision_service.reject(candidate_id, actor, note)

    def hold_candidate(self, candidate_id: str, actor: str, note: Optional[str] = None):
        return self.decision_service.hold(candidate_id, actor, note)

    def reopen_candidate(self, candidate_id: str, actor: str, note: Optional[str] = None):
        return self.decision_service.reopen(candidate_id, actor, note)

    def add_operator_note(self, candidate_id: str, actor: str, note: str):
        return self.decision_service.add_note(candidate_id, actor, note)
        
    # --- Alias Dictionary Operations ---

    def list_aliases(self) -> List[AliasRecord]:
        return self.alias_repo.get_all_enabled_aliases()
        
    def add_alias(self, actor: str, alias_type: str, token: str, resolution: str, source_platform: Optional[str] = None):
        alias_id = f"alias_{uuid.uuid4().hex[:12]}"
        record = AliasRecord(
            alias_id=alias_id,
            alias_type=alias_type,
            token=token,
            resolution=resolution,
            source_platform=source_platform,
            enabled=True
        )
        self.alias_repo.save_alias(record)
        
        # Log it as an audit event
        self.decision_service._record_audit(
            candidate_id="global",
            actor=actor,
            action="alias_add",
            reason=f"Added {alias_type} alias '{token}' -> '{resolution}'",
            target_alias=alias_id
        )
        return alias_id
        
    def disable_alias(self, actor: str, alias_id: str):
        self.alias_repo.disable_alias(alias_id)
        self.decision_service._record_audit(
            candidate_id="global",
            actor=actor,
            action="alias_disable",
            reason=f"Disabled alias {alias_id}",
            target_alias=alias_id
        )
