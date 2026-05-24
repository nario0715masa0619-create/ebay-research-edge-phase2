from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ReadinessResult(BaseModel):
    is_ready: bool
    readiness_score: float
    readiness_reasons: List[str]
    readiness_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReadinessChecker:
    """
    Evaluates whether a candidate is ready to be formulated into an ExecutionPayload.
    Checks 5 dimensions: seller_valid, sku_valid, content_complete, pricing_valid, state_clear.
    """
    
    def check_readiness(
        self,
        candidate_data: Dict[str, Any],
        seller_data: Dict[str, Any],
        handoff_data: Dict[str, Any]
    ) -> ReadinessResult:
        reasons = []
        score = 100.0
        
        # 1. seller_valid
        if not seller_data.get('is_active', False):
            reasons.append("seller_invalid: Seller account is not active or authorized.")
            score -= 20.0
            
        # 2. sku_valid
        if not candidate_data.get('sku'):
            reasons.append("sku_missing: Candidate SKU is missing or empty.")
            score -= 20.0
            
        # 3. content_complete
        if not self._is_content_complete(candidate_data):
            reasons.append("content_incomplete: Required content (title, aspects, etc) is missing.")
            score -= 20.0
            
        # 4. pricing_valid
        if candidate_data.get('profitability_score', 0) <= 0:
            reasons.append("pricing_conflict: Profitability score is 0 or negative.")
            score -= 20.0
            
        # 5. state_clear
        # If the handoff is not in an executable state (e.g., still processing or blocked)
        # Note: In reality, handoff status might already be guarded, but ReadinessChecker performs a final sanity check.
        status = handoff_data.get('handoff_status', '')
        if status in ['pending', 'processing', 'failed', 'rejected', 'deferred']:
            reasons.append(f"state_pending: Handoff status is '{status}', not ready for payload creation.")
            score -= 20.0
            
        # Hard fail if any critical score drop
        is_ready = score == 100.0
        
        return ReadinessResult(
            is_ready=is_ready,
            readiness_score=score,
            readiness_reasons=reasons
        )

    def _is_content_complete(self, candidate_data: Dict[str, Any]) -> bool:
        """Helper to determine if content is complete."""
        # Check basic fields
        if not candidate_data.get('title'):
            return False
        # Optional: verify category, condition, aspects etc.
        return True
