from typing import Dict, Any, Optional
from src.ebay.models import ProductCandidate
from .category_resolver import CategoryResolutionResult
from .aspects_resolver import AspectsResolutionResult
from .condition_resolver import ConditionResolutionResult
from .policy_evaluator import PolicyReadinessResult

class ListingPayloadDraftBuilder:
    def build_inventory_item_draft(
        self,
        candidate: ProductCandidate,
        aspects_res: AspectsResolutionResult,
        condition_res: ConditionResolutionResult
    ) -> Dict[str, Any]:
        return {
            "sku": candidate.sku,
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": 1 # Default
                }
            },
            "condition": condition_res.ebay_condition,
            "product": {
                "title": candidate.ebay_title_candidate or candidate.normalized_title or candidate.source_title,
                "description": f"Product from {candidate.source_platform}. URL: {candidate.source_url}",
                "aspects": aspects_res.ebay_aspects_json,
                "imageUrls": candidate.image_urls
            }
        }

    def build_offer_draft(
        self,
        candidate: ProductCandidate,
        category_res: CategoryResolutionResult,
        policy_res: PolicyReadinessResult,
        marketplace_id: str = "EBAY_US"
    ) -> Dict[str, Any]:
        return {
            "sku": candidate.sku,
            "marketplaceId": marketplace_id,
            "format": "FIXED_PRICE",
            "categoryId": category_res.ebay_category_id,
            "availableQuantity": 1,
            "pricingSummary": {
                "price": {
                    "value": str(round(candidate.expected_sale_price_usd, 2)),
                    "currency": "USD"
                }
            },
            "listingDuration": "GTC",
            "merchantLocationKey": policy_res.merchant_location_key,
            "listingPolicies": {
                "fulfillmentPolicyId": policy_res.fulfillment_policy_id,
                "paymentPolicyId": policy_res.payment_policy_id,
                "returnPolicyId": policy_res.return_policy_id
            }
        }
