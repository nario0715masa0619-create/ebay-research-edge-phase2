from dataclasses import dataclass, field
from typing import List, Tuple
from src.ebay.models import ProductCandidate
from .models import ListingExecutionRequest

@dataclass
class GuardResult:
    allowed_flag: bool = False
    guard_blockers: List[str] = field(default_factory=list)
    guard_reason_codes: List[str] = field(default_factory=list)
    skip_flag: bool = False
    recommended_status: str = "failed"

class CandidateExecutionGuard:
    def validate(self, candidate: ProductCandidate, request: ListingExecutionRequest) -> GuardResult:
        blockers = []
        skip = False
        
        # Section 6: 実行対象条件
        if candidate.pipeline_type != "auto":
            blockers.append("manual_preban_not_allowed" if candidate.pipeline_type == "manual_preban" else "not_auto_pipeline")
            skip = True
            
        if candidate.listing_readiness_status != "ready" and not request.force_republish:
             blockers.append("candidate_not_ready")
             skip = True
             
        if not candidate.publish_readiness and not request.force_republish:
            blockers.append("publish_readiness_false")
            skip = True
            
        allowed_statuses = ["approved", "listing_ready", "candidate"]
        if candidate.status not in allowed_statuses and not request.force_republish:
            if candidate.status == "listed":
                blockers.append("already_listed")
                skip = True
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
            
        # Decide status
        status = "failed"
        if skip:
            status = "skipped"
        elif any(k in "".join(blockers) for k in ["policy", "location"]):
            status = "review_required"
            
        return GuardResult(
            allowed_flag=len(blockers) == 0,
            guard_blockers=blockers,
            guard_reason_codes=blockers,
            skip_flag=skip,
            recommended_status=status
        )
