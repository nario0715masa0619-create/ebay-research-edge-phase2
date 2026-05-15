from typing import Optional, List
from src.ebay.models import EbayListing

class EbayListingRepository:
    def __init__(self):
        self._listings = {}  # {sku: EbayListing}
        self._candidate_map = {} # {candidate_id: sku}

    def get_by_sku(self, sku: str) -> Optional[EbayListing]:
        return self._listings.get(sku)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[EbayListing]:
        sku = self._candidate_map.get(candidate_id)
        if sku:
            return self.get_by_sku(sku)
        return None

    def upsert(self, listing: EbayListing):
        self._listings[listing.sku] = listing
        self._candidate_map[listing.candidate_id] = listing.sku

    def list_all(self) -> List[EbayListing]:
        return list(self._listings.values())
