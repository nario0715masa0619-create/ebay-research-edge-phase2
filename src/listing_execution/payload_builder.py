"""
Builds ExecutionPayload from CSV row and resolved images.
"""
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from src.listing_execution.csv_loader import ListingRow
from src.listing_execution.image_resolver import SkuImageResolver, ImageValidationResult
from src.listing_execution.models.execution_payload import ExecutionPayload
import logging
import uuid

logger = logging.getLogger(__name__)

class PayloadBuildError(Exception):
    pass

class EBayListingPayloadBuilder:
    def __init__(
        self,
        image_resolver: Optional[SkuImageResolver] = None,
        default_category_id: str = "6000",
        default_currency: str = "USD"
    ):
        self.image_resolver = image_resolver or SkuImageResolver()
        self.default_category_id = default_category_id
        self.default_currency = default_currency
    
    def build(
        self,
        listing_row: ListingRow,
        seller: str,
        environment: str = "sandbox",
        dry_run: bool = True,
        category_id: Optional[str] = None
    ) -> Optional[ExecutionPayload]:
        try:
            image_result = self.image_resolver.resolve(listing_row.sku)
            
            if not image_result.is_valid:
                logger.warning(
                    f"SKU {listing_row.sku}: Image validation failed: {image_result.errors}"
                )
                return None
            
            # Using absolute path string format
            image_urls = [str(p) for p in image_result.image_paths]
            
            # Injecting default values for Pydantic fields
            # bundle_state, market_eval, profitability_score
            payload = ExecutionPayload(
                listing_id=str(uuid.uuid4()),
                attempt_id=f"att_{datetime.now().timestamp():.0f}_{listing_row.sku}",
                seller=seller,
                environment=environment,
                sku=listing_row.sku,
                category_id=category_id or self.default_category_id,
                title=listing_row.title,
                description=listing_row.description,
                price=listing_row.price,
                currency=self.default_currency,
                condition=listing_row.condition,
                condition_description=None,
                brand=listing_row.brand,
                mpn=listing_row.mpn,
                image_urls=image_urls,
                item_specifics={},
                shipping_profile_id=None,
                return_profile_id=None,
                payment_profile_id=None,
                format="fixed_price",
                quantity=listing_row.quantity,
                dry_run=dry_run,
                bundle_state="standalone",
                market_eval={},
                profitability_score=0.0
            )
            
            logger.info(
                f"SKU {listing_row.sku}: Payload built successfully with {len(image_urls)} images"
            )
            return payload
        
        except Exception as e:
            logger.error(f"SKU {listing_row.sku}: Failed to build payload: {str(e)}")
            return None
