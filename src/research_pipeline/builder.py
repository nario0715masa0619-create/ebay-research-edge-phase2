import hashlib
import uuid
from typing import Dict, Any, List
from src.ebay.models import SourceItem, ProductCandidate

class CandidateBuilder:
    def build_initial_candidate(self, source_item: SourceItem) -> ProductCandidate:
        candidate_id = str(uuid.uuid4())
        sku = self.generate_sku(source_item)
        
        # Basic normalization (placeholders for more advanced logic)
        normalized_title = self._normalize_title(source_item.source_title)
        
        return ProductCandidate(
            candidate_id=candidate_id,
            source_item_id=source_item.source_item_id,
            source_platform=source_item.source_platform,
            sku=sku,
            source_url=source_item.source_url,
            source_title=source_item.source_title,
            source_price_jpy=source_item.source_price_jpy,
            source_shipping_jpy=source_item.source_shipping_jpy,
            source_stock_status=source_item.source_stock_status,
            source_purchase_type=source_item.source_purchase_type,
            image_urls=source_item.source_image_urls,
            normalized_title=normalized_title,
            status="normalized"
        )

    def generate_sku(self, source_item: SourceItem) -> str:
        # Rules: prefix AUTO - SERIES - CHAR - PROD - ID_HASH
        prefix = "AUTO"
        platform_code = source_item.source_platform[:2].upper()
        
        # Simple stable hash of source_item_id
        id_hash = hashlib.md5(source_item.source_item_id.encode()).hexdigest()[:8].upper()
        
        # Placeholder for actual series/char extraction
        series = "GEN"
        char = "GEN"
        prod = "ITEM"
        
        return f"{prefix}-{platform_code}-{series}-{char}-{prod}-{id_hash}"

    def _normalize_title(self, title: str) -> str:
        # TODO: More advanced NLP / pattern matching
        return title.strip()
