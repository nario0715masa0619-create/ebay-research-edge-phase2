from typing import Dict, Any, List, Optional
from src.ebay.models import ProductCandidate, EbayListing

class StateComparator:
    def compare(self, candidate: ProductCandidate, listing: Optional[EbayListing], remote_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares DB state vs Remote state and identifies drifts.
        """
        drifts = []
        remote_offer = remote_state.get("offer")
        remote_inv = remote_state.get("inventory_item")

        # 1. Existence check
        if not remote_offer:
            drifts.append("offer_missing_remote")
        if not remote_inv:
            drifts.append("inventory_missing_remote")

        # 2. ID drifts
        if remote_offer:
            remote_offer_id = remote_offer.get("offerId")
            remote_listing_id = remote_offer.get("listingId")
            
            if listing:
                if listing.offer_id != remote_offer_id:
                    drifts.append("offer_id_drift")
                if listing.listing_id != remote_listing_id and remote_listing_id:
                    drifts.append("missing_listing_id_in_db")
            else:
                drifts.append("missing_ebay_listing_row")

        # 3. Status drifts
        if remote_offer:
            remote_offer_status = remote_offer.get("status") # 'PUBLISHED', 'UNPUBLISHED'
            # Note: eBay Inventory API uses 'PUBLISHED' for active listings
            
            db_status = candidate.status # 'listed', 'approved', etc.
            
            if remote_offer_status == "PUBLISHED" and db_status != "listed":
                drifts.append("db_marked_inactive_but_remote_published")
            elif remote_offer_status == "UNPUBLISHED" and db_status == "listed":
                drifts.append("db_marked_listed_but_remote_unpublished")

        # 4. Price & Quantity drifts
        if remote_offer and listing:
            remote_price = float(remote_offer.get("pricingSummary", {}).get("price", {}).get("value", 0))
            if abs(remote_price - listing.listing_price_usd) > 0.01:
                drifts.append("price_drift")
        
        if remote_inv and listing:
            remote_qty = remote_inv.get("availableQuantity", 0)
            if remote_qty != listing.quantity:
                drifts.append("quantity_drift")

        return {
            "drifts": drifts,
            "severity": "high" if drifts else "none",
            "remote_offer_found": remote_offer is not None,
            "remote_inventory_found": remote_inv is not None
        }
