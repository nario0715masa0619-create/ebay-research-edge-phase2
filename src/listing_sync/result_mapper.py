from typing import Any, Dict
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
        
    def update_candidate_from_sync(self, candidate: ProductCandidate, result_status: str, review_required: bool):
        """
        Updates ProductCandidate based on sync result.
        """
        if review_required:
            candidate.status = "review_required"
            candidate.decision_type = "review_required"
        
        if result_status == "synced" or result_status == "repaired":
            # If it was in error, maybe bring it back? 
            # For now, just mark it as researched/listed if it's published
            pass
