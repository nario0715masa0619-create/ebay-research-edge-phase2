from typing import List, Optional
from src.ebay.models import ProductCandidate, EbayListing

class SyncTargetSelector:
    def evaluate(self, candidate: ProductCandidate, listing: Optional[EbayListing], force_recheck: bool = False) -> bool:
        """
        Determines if a candidate should be synced.
        """
        # 1. Force recheck always wins
        if force_recheck:
            return True

        # 2. Exclude non-targets
        if candidate.pipeline_type == "manual_preban" or candidate.decision_type == "excluded":
            return False
        
        # 3. Targets based on status
        # If DB says listed but we need to verify
        if candidate.status in ["listed", "paused"]:
            return True

        # If it was in the middle of readiness/execution and has an offer_id/sku
        if candidate.listing_readiness_status == "ready" or candidate.status == "approved":
            if candidate.sku or (listing and listing.offer_id):
                return True

        # If it has an active listing but status is not synced
        if listing and listing.listing_id:
            return True

        return False
