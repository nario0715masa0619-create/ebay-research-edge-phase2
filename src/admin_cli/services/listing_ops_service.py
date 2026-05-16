from typing import List, Optional, Dict, Any
from src.repositories.persistent_ebay_listing_repository import PersistentEbayListingRepository
from src.listing_sync.gateway import ListingSyncRecoveryGateway, ListingSyncRequest
from ..models import CliCommandResult

class ListingOpsService:
    def __init__(self, listing_repo: PersistentEbayListingRepository, sync_gateway: ListingSyncRecoveryGateway):
        self.listing_repo = listing_repo
        self.sync_gateway = sync_gateway

    def list_listings(self, limit: int = 20) -> List[Dict[str, Any]]:
        listings = self.listing_repo.list_active(limit=limit)
        return [
            {
                "sku": l.sku,
                "listing_id": l.listing_id or "-",
                "offer_status": l.offer_status,
                "listing_status": l.listing_status or "-",
                "price": f"{l.listing_price_usd:.2f} USD",
                "quantity": l.quantity,
                "listed_at": l.listed_at.isoformat() if l.listed_at else "-"
            }
            for l in listings
        ]

    def sync_listing(self, sku: str, dry_run: bool = True, force_recheck: bool = False) -> CliCommandResult:
        listing = self.listing_repo.get_by_sku(sku)
        if not listing:
            return CliCommandResult(command_path="listings sync", status="error", errors=[f"Listing with SKU '{sku}' not found."], exit_code=2)
        
        req = ListingSyncRequest(
            candidate_id=listing.candidate_id,
            sku=sku,
            dry_run=dry_run,
            force_recheck=force_recheck
        )
        
        res = self.sync_gateway.sync_and_recover_listing(req)
        
        return CliCommandResult(
            command_path="listings sync",
            message=f"Sync completed for SKU '{sku}'.",
            summary={
                "sync_status": res.sync_status,
                "success": res.success_flag,
                "review_required": res.review_required_flag,
                "drift_count": len(res.drift_types)
            },
            meta={"drifts": res.drift_types},
            exit_code=0 if res.success_flag else 4
        )
