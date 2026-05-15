from datetime import datetime
from typing import Optional
from src.ebay.models import ProductCandidate, EbayListing
from .models import ListingExecutionResult

class ExecutionResultMapper:
    def map_to_listing(self, candidate: ProductCandidate, res: ListingExecutionResult) -> EbayListing:
        listing = EbayListing(
            sku=candidate.sku,
            candidate_id=candidate.candidate_id,
            marketplace_id=res.listing_id or "UNKNOWN", # Actually marketplace_id should come from request
            inventory_item_status=res.inventory_item_status,
            offer_id=res.offer_id,
            offer_status=res.offer_status,
            listing_id=res.listing_id,
            listing_price_usd=candidate.expected_sale_price_usd,
            last_publish_attempt_at=datetime.now(),
            last_publish_error=res.error_summary,
            updated_at=datetime.now()
        )
        
        offer_draft = candidate.offer_draft_json
        listing.merchant_location_key = offer_draft.get("merchantLocationKey")
        policies = offer_draft.get("listingPolicies", {})
        listing.fulfillment_policy_id = policies.get("fulfillmentPolicyId")
        listing.payment_policy_id = policies.get("paymentPolicyId")
        listing.return_policy_id = policies.get("returnPolicyId")
        
        if res.publish_status == "published":
            listing.listed_at = datetime.now()
            
        return listing

    def update_candidate(self, candidate: ProductCandidate, res: ListingExecutionResult):
        candidate.updated_at = datetime.now()
        candidate.last_checked_at = datetime.now()
        
        if res.execution_status == "succeeded":
            candidate.status = "listed"
        elif res.review_required_flag:
            candidate.decision_reason_codes.append("publish_review_required")
            # Keep status or move to review_required if needed
        elif res.retryable_flag:
            candidate.decision_reason_codes.append("publish_retryable_error")
