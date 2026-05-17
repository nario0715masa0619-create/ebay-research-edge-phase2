from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import SellerPolicySnapshotModel
from src.seller_env.models import SellerPolicySnapshot

class PersistentSellerPolicySnapshotRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, snapshot: SellerPolicySnapshot):
        model = SellerPolicySnapshotModel(
            snapshot_id=snapshot.snapshot_id,
            seller_account_id=snapshot.seller_account_id,
            environment_id=snapshot.environment_id,
            marketplace_id=snapshot.marketplace_id,
            fulfillment_policy_id=snapshot.fulfillment_policy_id,
            payment_policy_id=snapshot.payment_policy_id,
            return_policy_id=snapshot.return_policy_id,
            payload_json=snapshot.payload,
            fetched_at=snapshot.fetched_at
        )
        self.session.add(model)
        self.session.flush()

    def get_latest(self, seller_account_id: str, marketplace_id: str) -> Optional[SellerPolicySnapshot]:
        stmt = select(SellerPolicySnapshotModel).where(
            SellerPolicySnapshotModel.seller_account_id == seller_account_id,
            SellerPolicySnapshotModel.marketplace_id == marketplace_id
        ).order_by(SellerPolicySnapshotModel.fetched_at.desc()).limit(1)
        
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def _to_domain(self, model: SellerPolicySnapshotModel) -> SellerPolicySnapshot:
        return SellerPolicySnapshot(
            snapshot_id=model.snapshot_id,
            seller_account_id=model.seller_account_id,
            environment_id=model.environment_id,
            marketplace_id=model.marketplace_id,
            fulfillment_policy_id=model.fulfillment_policy_id,
            payment_policy_id=model.payment_policy_id,
            return_policy_id=model.return_policy_id,
            payload=model.payload_json,
            fetched_at=model.fetched_at
        )
