from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from src.change_mgmt.models.change_proposal import (
    ChangeProposal, ChangeType, ChangeScopeType, RiskLevel, 
    ProposalStatus, ValidationStatus
)

class ChangeProposalService:
    """Change proposal 管理"""
    
    def __init__(self):
        self.proposals: Dict[UUID, ChangeProposal] = {}

    def create_proposal_from_recommendation(
        self, recommendation_id: UUID, title: str, summary: str, 
        change_type: ChangeType, target_component: str, 
        scope_type: ChangeScopeType, scope_target_id: Optional[str], 
        risk_level: RiskLevel, created_by: str
    ) -> ChangeProposal:
        
        proposal = ChangeProposal(
            change_proposal_id=uuid4(),
            source_recommendation_id=recommendation_id,
            title=title,
            summary=summary,
            target_phase="Unknown",
            target_component=target_component,
            change_type=change_type,
            change_scope_type=scope_type,
            scope_target_id=scope_target_id,
            risk_level=risk_level,
            proposal_status=ProposalStatus.PROPOSED,
            validation_status=ValidationStatus.PENDING,
            rollout_status="not_started",
            validation_strategy="manual_observation",
            rollback_strategy="config_snapshot_revert",
            created_by=created_by,
            created_at=datetime.utcnow(),
            review_due_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            cancelled_at=None,
            metadata_json={}
        )
        self.proposals[proposal.change_proposal_id] = proposal
        return proposal

    def create_manual_proposal(
        self, title: str, summary: str, change_type: ChangeType, 
        target_component: str, scope_type: ChangeScopeType, 
        scope_target_id: Optional[str], risk_level: RiskLevel, 
        validation_strategy: str, rollback_strategy: str, created_by: str
    ) -> ChangeProposal:
        
        proposal = ChangeProposal(
            change_proposal_id=uuid4(),
            source_recommendation_id=None,
            title=title,
            summary=summary,
            target_phase="Unknown",
            target_component=target_component,
            change_type=change_type,
            change_scope_type=scope_type,
            scope_target_id=scope_target_id,
            risk_level=risk_level,
            proposal_status=ProposalStatus.PROPOSED,
            validation_status=ValidationStatus.PENDING,
            rollout_status="not_started",
            validation_strategy=validation_strategy,
            rollback_strategy=rollback_strategy,
            created_by=created_by,
            created_at=datetime.utcnow(),
            review_due_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            cancelled_at=None,
            metadata_json={}
        )
        self.proposals[proposal.change_proposal_id] = proposal
        return proposal

    def get_proposal_by_id(self, change_proposal_id: UUID) -> Optional[ChangeProposal]:
        return self.proposals.get(change_proposal_id)

    def list_proposals(
        self, status: Optional[ProposalStatus] = None, 
        change_type: Optional[ChangeType] = None, 
        risk_level: Optional[RiskLevel] = None, 
        target_phase: Optional[str] = None, 
        limit: int = 100, offset: int = 0
    ) -> Tuple[List[ChangeProposal], int]:
        
        filtered = list(self.proposals.values())
        if status:
            filtered = [p for p in filtered if p.proposal_status == status]
        if change_type:
            filtered = [p for p in filtered if p.change_type == change_type]
        if risk_level:
            filtered = [p for p in filtered if p.risk_level == risk_level]
        if target_phase:
            filtered = [p for p in filtered if p.target_phase == target_phase]
            
        total = len(filtered)
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[offset:offset+limit], total

    def update_proposal_status(self, change_proposal_id: UUID, new_status: ProposalStatus, actor_id: str) -> Tuple[ChangeProposal, Dict[str, Any]]:
        proposal = self.proposals[change_proposal_id]
        if proposal.proposal_status == ProposalStatus.REJECTED or proposal.proposal_status == ProposalStatus.CANCELLED:
            raise ValueError("Cannot update rejected or cancelled proposal")
            
        old_status = proposal.proposal_status
        proposal.proposal_status = new_status
        
        event = {
            "proposal_id": proposal.change_proposal_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "actor_id": actor_id,
            "timestamp": datetime.utcnow()
        }
        return proposal, event

    def approve_proposal(self, change_proposal_id: UUID, approved_by: str) -> Tuple[ChangeProposal, Dict[str, Any]]:
        proposal = self.proposals[change_proposal_id]
        proposal.approved_by = approved_by
        proposal.approved_at = datetime.utcnow()
        return self.update_proposal_status(change_proposal_id, ProposalStatus.APPROVED, approved_by)

    def reject_proposal(self, change_proposal_id: UUID, rejected_by: str, reason: str) -> Tuple[ChangeProposal, Dict[str, Any]]:
        proposal = self.proposals[change_proposal_id]
        proposal.rejected_by = rejected_by
        proposal.rejected_at = datetime.utcnow()
        proposal.metadata_json["reject_reason"] = reason
        old_status = proposal.proposal_status
        proposal.proposal_status = ProposalStatus.REJECTED
        
        event = {
            "proposal_id": proposal.change_proposal_id,
            "old_status": old_status.value,
            "new_status": ProposalStatus.REJECTED.value,
            "actor_id": rejected_by,
            "reason": reason,
            "timestamp": datetime.utcnow()
        }
        return proposal, event

    def count_proposals_by_status(self) -> Dict[ProposalStatus, int]:
        counts = {}
        for p in self.proposals.values():
            counts[p.proposal_status] = counts.get(p.proposal_status, 0) + 1
        return counts
