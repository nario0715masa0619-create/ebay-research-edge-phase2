from typing import Tuple, List, Optional
from src.ebay.models import ProductCandidate

class CandidateDecisionEngine:
    def decide(self, candidate: ProductCandidate, strictness: str = "balanced") -> Tuple[str, str, Optional[str], List[str]]:
        """
        Returns: (pipeline_type, decision_type, exclude_reason, reason_codes)
        """
        pipeline_type = "auto"
        decision_type = "candidate"
        exclude_reason = None
        reason_codes = []

        # 1. Entrance Logic
        if candidate.source_platform == "pbandai":
            pipeline_type = "manual_preban"
            decision_type = "excluded"
            exclude_reason = "preban"
            reason_codes.append("source_is_pbandai")
            return pipeline_type, decision_type, exclude_reason, reason_codes

        if candidate.source_purchase_type != "buy_now":
            decision_type = "excluded"
            exclude_reason = "not_buy_now"
            reason_codes.append("requires_auction_or_negotiation")

        if candidate.source_stock_status != "in_stock":
            decision_type = "excluded"
            exclude_reason = "out_of_stock"
            reason_codes.append("out_of_stock")

        # Preorder / Lottery / Unreleased checks (Search keywords in title for now)
        forbidden_keywords = ["preorder", "lottery", "unreleased", "予約", "抽選", "未発売"]
        lower_title = (candidate.source_title or "").lower()
        if any(k in lower_title for k in forbidden_keywords):
            decision_type = "excluded"
            exclude_reason = "forbidden_status"
            reason_codes.append("preorder_lottery_or_unreleased_detected")

        # 2. Financial Logic
        # These would be based on TotalCostResult / StandardScoreResult integrated into candidate
        if candidate.expected_profit_rate < 0.1: # Example 10%
            if decision_type != "excluded":
                decision_type = "excluded"
                exclude_reason = "low_margin"
                reason_codes.append("margin_below_threshold")

        if candidate.standard_score < 40: # Example Grade E
            if decision_type != "excluded":
                decision_type = "excluded"
                exclude_reason = "low_score"
                reason_codes.append("quality_score_below_threshold")

        # 3. Quality Logic
        if not candidate.normalized_title:
            decision_type = "review_required"
            reason_codes.append("title_normalization_failed")

        if not candidate.image_urls:
            decision_type = "excluded"
            exclude_reason = "insufficient_images"
            reason_codes.append("no_images_available")

        # Status Update
        if decision_type == "excluded":
            candidate.status = "excluded"
        elif decision_type == "review_required":
            candidate.status = "researched" # Ready for review
        else:
            candidate.status = "candidate"

        return pipeline_type, decision_type, exclude_reason, reason_codes
