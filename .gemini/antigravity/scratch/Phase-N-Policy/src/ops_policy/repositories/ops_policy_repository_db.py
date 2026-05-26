from typing import Optional, List, Tuple, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel
from src.db.models import OpsPolicyModel
from datetime import datetime

class OpsPolicyRepository:
    """DB-backed policy repository"""

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: OpsPolicyModel) -> OpsPolicy:
        return OpsPolicy(
            policy_id=model.policy_id,
            scope_type=ScopeType(model.scope_type),
            target_id=model.target_id,
            action_type=ActionType(model.action_type),
            level=PolicyLevel(model.level),
            status=PolicyStatus(model.status),
            title=model.title,
            reason_summary=model.reason_summary,
            evidence_summary=model.evidence_summary,
            linked_incident_id=model.linked_incident_id,
            effective_from=model.effective_from,
            effective_until=model.effective_until,
            review_due_at=model.review_due_at,
            created_by=model.created_by,
            approved_by=model.approved_by,
            applied_at=model.applied_at,
            released_at=model.released_at,
            is_expired=model.is_expired,
            priority=model.priority,
            metadata_json=model.metadata_json
        )

    def _to_model(self, entity: OpsPolicy) -> OpsPolicyModel:
        return OpsPolicyModel(
            policy_id=entity.policy_id,
            scope_type=entity.scope_type.value,
            target_id=entity.target_id,
            action_type=entity.action_type.value,
            level=entity.level.value,
            status=entity.status.value,
            title=entity.title,
            reason_summary=entity.reason_summary,
            evidence_summary=entity.evidence_summary,
            linked_incident_id=entity.linked_incident_id,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            review_due_at=entity.review_due_at,
            created_by=entity.created_by,
            approved_by=entity.approved_by,
            applied_at=entity.applied_at,
            released_at=entity.released_at,
            is_expired=entity.is_expired,
            priority=entity.priority,
            metadata_json=entity.metadata_json,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def create_policy(self, policy: OpsPolicy) -> OpsPolicy:
        model = self._to_model(policy)
        self.session.add(model)
        self.session.commit()
        return policy

    def get_policy_by_id(self, policy_id: UUID) -> Optional[OpsPolicy]:
        model = self.session.query(OpsPolicyModel).filter_by(policy_id=policy_id).first()
        return self._to_entity(model) if model else None

    def update_policy(self, policy: OpsPolicy) -> OpsPolicy:
        model = self.session.query(OpsPolicyModel).filter_by(policy_id=policy.policy_id).first()
        if not model:
            raise ValueError("Policy not found")
            
        model.status = policy.status.value
        model.effective_until = policy.effective_until
        model.review_due_at = policy.review_due_at
        model.approved_by = policy.approved_by
        model.applied_at = policy.applied_at
        model.released_at = policy.released_at
        model.is_expired = policy.is_expired
        model.updated_at = datetime.utcnow()
        
        self.session.commit()
        return policy

    def list_policies(self, scope_type: Optional[ScopeType] = None, status: Optional[PolicyStatus] = None, seller_account_id: Optional[str] = None, environment: Optional[str] = None, limit: int = 100, offset: int = 0) -> Tuple[List[OpsPolicy], int]:
        q = self.session.query(OpsPolicyModel)
        
        if scope_type:
            q = q.filter(OpsPolicyModel.scope_type == scope_type.value)
        if status:
            q = q.filter(OpsPolicyModel.status == status.value)
        if seller_account_id:
            q = q.filter(OpsPolicyModel.scope_type == ScopeType.SELLER.value, OpsPolicyModel.target_id == seller_account_id)
        if environment:
            q = q.filter(OpsPolicyModel.scope_type == ScopeType.ENVIRONMENT.value, OpsPolicyModel.target_id == environment)
            
        total = q.count()
        models = q.order_by(OpsPolicyModel.created_at.desc()).offset(offset).limit(limit).all()
        return [self._to_entity(m) for m in models], total

    def get_active_policies(self, seller_account_id: Optional[str] = None, environment: Optional[str] = None) -> List[OpsPolicy]:
        q = self.session.query(OpsPolicyModel).filter(OpsPolicyModel.status == PolicyStatus.ACTIVE.value)
        
        if seller_account_id:
            q = q.filter(OpsPolicyModel.scope_type == ScopeType.SELLER.value, OpsPolicyModel.target_id == seller_account_id)
        if environment:
            q = q.filter(OpsPolicyModel.scope_type == ScopeType.ENVIRONMENT.value, OpsPolicyModel.target_id == environment)
            
        return [self._to_entity(m) for m in q.all()]

    def count_policies_by_status(self) -> Dict[PolicyStatus, int]:
        rows = self.session.query(OpsPolicyModel.status, func.count(OpsPolicyModel.policy_id)).group_by(OpsPolicyModel.status).all()
        return {PolicyStatus(status): count for status, count in rows}

    def get_policies_by_scope_type(self, scope_type: ScopeType) -> List[OpsPolicy]:
        models = self.session.query(OpsPolicyModel).filter(OpsPolicyModel.scope_type == scope_type.value).all()
        return [self._to_entity(m) for m in models]

    def get_policies_by_action_type(self, action_type: ActionType) -> List[OpsPolicy]:
        models = self.session.query(OpsPolicyModel).filter(OpsPolicyModel.action_type == action_type.value).all()
        return [self._to_entity(m) for m in models]

    def get_seller_policies(self, seller_account_id: str) -> List[OpsPolicy]:
        models = self.session.query(OpsPolicyModel).filter(
            OpsPolicyModel.scope_type == ScopeType.SELLER.value,
            OpsPolicyModel.target_id == seller_account_id
        ).all()
        return [self._to_entity(m) for m in models]

    def get_environment_policies(self, environment: str) -> List[OpsPolicy]:
        models = self.session.query(OpsPolicyModel).filter(
            OpsPolicyModel.scope_type == ScopeType.ENVIRONMENT.value,
            OpsPolicyModel.target_id == environment
        ).all()
        return [self._to_entity(m) for m in models]
