from typing import List, Tuple
from src.ebay.models import ProductCandidate
from .models import ListingExecutionRequest

class CandidateExecutionGuard:
    def validate(self, candidate: ProductCandidate, request: ListingExecutionRequest) -> Tuple[bool, List[str]]:
        blockers = []
        
        # Section 6: 実行対象条件
        if candidate.pipeline_type != "auto":
            blockers.append("manual_preban_not_allowed" if candidate.pipeline_type == "manual_preban" else "not_auto_pipeline")
            
        if candidate.listing_readiness_status != "ready" and not request.force_republish:
             blockers.append("candidate_not_ready")
             
        if not candidate.publish_readiness and not request.force_republish:
            blockers.append("publish_readiness_false")
            
        allowed_statuses = ["approved", "listing_ready", "candidate"]
        if candidate.status not in allowed_statuses and not request.force_republish:
            if candidate.status == "listed":
                blockers.append("already_listed")
            else:
                blockers.append("invalid_candidate_status")

        # Section 9.2: 必須データ確認
        if not candidate.inventory_item_draft_json:
            blockers.append("missing_inventory_item_draft")
        if not candidate.offer_draft_json:
            blockers.append("missing_offer_draft")
            
        # Check location and policies in offer draft
        offer = candidate.offer_draft_json
        if not offer.get("merchantLocationKey"):
            blockers.append("missing_location")
            
        policies = offer.get("listingPolicies", {})
        if not policies.get("paymentPolicyId"):
            blockers.append("missing_payment_policy")
        if not policies.get("returnPolicyId"):
            blockers.append("missing_return_policy")
        if not policies.get("fulfillmentPolicyId"):
            blockers.append("missing_fulfillment_policy")
            
        return len(blockers) == 0, blockers
