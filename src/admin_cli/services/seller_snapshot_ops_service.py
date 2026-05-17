from typing import List, Dict, Any, Optional
from src.repositories.persistent_seller_policy_snapshot_repository import PersistentSellerPolicySnapshotRepository
from src.repositories.persistent_seller_location_snapshot_repository import PersistentSellerLocationSnapshotRepository

class SellerSnapshotOpsService:
    def __init__(self, policy_repo, location_repo):
        self.policy_repo = policy_repo
        self.location_repo = location_repo

    def get_latest_policies(self, seller_account_id: str, marketplace_id: str) -> Optional[Dict[str, Any]]:
        snap = self.policy_repo.get_latest(seller_account_id, marketplace_id)
        if not snap: return None
        return {
            "seller_id": snap.seller_account_id,
            "marketplace": snap.marketplace_id,
            "fulfillment": snap.fulfillment_policy_id,
            "payment": snap.payment_policy_id,
            "return": snap.return_policy_id,
            "fetched_at": snap.fetched_at.isoformat(),
            "payload": snap.payload
        }

    def get_latest_locations(self, seller_account_id: str, merchant_location_key: str) -> Optional[Dict[str, Any]]:
        snap = self.location_repo.get_latest(seller_account_id, merchant_location_key)
        if not snap: return None
        return {
            "seller_id": snap.seller_account_id,
            "location_key": snap.merchant_location_key,
            "fetched_at": snap.fetched_at.isoformat(),
            "payload": snap.payload
        }
