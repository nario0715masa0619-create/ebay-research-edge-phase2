from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import SellerLocationSnapshotModel
from src.seller_env.models import SellerLocationSnapshot

class PersistentSellerLocationSnapshotRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, snapshot: SellerLocationSnapshot):
        model = SellerLocationSnapshotModel(
            snapshot_id=snapshot.snapshot_id,
            seller_account_id=snapshot.seller_account_id,
            environment_id=snapshot.environment_id,
            merchant_location_key=snapshot.merchant_location_key,
            payload_json=snapshot.payload,
            fetched_at=snapshot.fetched_at
        )
        self.session.add(model)
        self.session.flush()

    def get_latest(self, seller_account_id: str, merchant_location_key: str) -> Optional[SellerLocationSnapshot]:
        stmt = select(SellerLocationSnapshotModel).where(
            SellerLocationSnapshotModel.seller_account_id == seller_account_id,
            SellerLocationSnapshotModel.merchant_location_key == merchant_location_key
        ).order_by(SellerLocationSnapshotModel.fetched_at.desc()).limit(1)
        
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def _to_domain(self, model: SellerLocationSnapshotModel) -> SellerLocationSnapshot:
        return SellerLocationSnapshot(
            snapshot_id=model.snapshot_id,
            seller_account_id=model.seller_account_id,
            environment_id=model.environment_id,
            merchant_location_key=model.merchant_location_key,
            payload=model.payload_json,
            fetched_at=model.fetched_at
        )
