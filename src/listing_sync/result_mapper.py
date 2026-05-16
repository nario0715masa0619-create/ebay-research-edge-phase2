from typing import Any, Dict, Optional
from datetime import datetime
from src.ebay.models import ProductCandidate, EbayListing

class SyncResultMapper:
    def update_listing_from_remote(self, listing: EbayListing, remote_offer: Dict[str, Any]):
        """
        Updates EbayListing object with remote state.
        """
        listing.offer_id = remote_offer.get("offerId")
        listing.listing_id = remote_offer.get("listingId")
        listing.offer_status = remote_offer.get("status")
        
        # pricingSummary.price.value
        price_val = remote_offer.get("pricingSummary", {}).get("price", {}).get("value")
        if price_val:
            listing.listing_price_usd = float(price_val)
            
        # listingStatus
        listing.listing_status = remote_offer.get("listingStatus")
        
        listing.updated_at = datetime.now()
        # Note: caller should set last_synced_at if applicable
        
    def update_candidate_from_sync(self, candidate: ProductCandidate, result_status: str, review_required: bool, remote_offer: Optional[Dict[str, Any]] = None):
        """
        Updates ProductCandidate based on sync result.
        """
        if review_required:
            candidate.status = "review_required"
            candidate.decision_type = "review_required"
            candidate.updated_at = datetime.now()
        
        if remote_offer:
            remote_status = remote_offer.get("status")
            if remote_status == "PUBLISHED":
                candidate.status = "listed"
            elif remote_status == "UNPUBLISHED":
                # If it was listed but now unpublished, mark as paused
                if candidate.status == "listed":
                    candidate.status = "paused"
        
        candidate.updated_at = datetime.now()
        
        if result_status == "synced" or result_status == "repaired":
            # If it was in error, maybe bring it back? 
            # For now, just mark it as researched/listed if it's published
            pass
