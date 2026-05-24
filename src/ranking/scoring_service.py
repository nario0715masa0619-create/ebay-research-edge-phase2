import uuid
from datetime import datetime
from typing import List, Optional

from src.ranking.models import RankingInput, ListingDecisionResult, DecisionClass, QueueType
from src.ranking.config import RankingSettings
from src.ranking.eligibility_gate import EligibilityGate
from src.ranking.staleness_policy import StalenessPolicy
from src.ranking.decision_engine import DecisionEngine
from src.ranking.ranking_components import RankingCalculator
from src.ranking.queue_allocator import QueueAllocator

class RankingScoringService:
    def __init__(self, settings: RankingSettings):
        self.settings = settings
        self.staleness_policy = StalenessPolicy(settings)
        self.eligibility_gate = EligibilityGate(settings, self.staleness_policy)
        self.decision_engine = DecisionEngine(settings)
        self.calculator = RankingCalculator(settings)
        self.allocator = QueueAllocator(settings)
        
    def evaluate(self, input_data: RankingInput, now: datetime = None) -> ListingDecisionResult:
        if now is None:
            now = datetime.utcnow()
            
        decision_id = f"rdec_{uuid.uuid4().hex[:12]}"
        explanation_lines: List[str] = []
        
        # 1. Gate Evaluation
        immediate_decision, block_reasons, is_blocked, is_stale = self.eligibility_gate.evaluate_gates(input_data, now)
        if block_reasons:
            explanation_lines.extend(block_reasons)
            
        # 2. Component Scoring
        score, components = self.calculator.calculate_score(input_data, is_stale, is_blocked)
        explanation_lines.append(f"Base Ranking Score calculated: {score:.2f}/100")
        
        # 3. Decision Engine
        decision, decision_reason = self.decision_engine.determine_decision(
            input_data, immediate_decision, block_reasons, is_blocked, is_stale
        )
        explanation_lines.append(f"Decision determined: {decision.value}. Reason: {decision_reason}")
        
        # 4. Queue Allocation
        queue_type, launch_bucket, review_bucket = self.allocator.allocate(
            decision, score, is_blocked, is_stale, input_data
        )
        explanation_lines.append(f"Assigned to Queue: {queue_type.value}")
        if launch_bucket:
            explanation_lines.append(f"Launch Priority Bucket: {launch_bucket.value}")
        if review_bucket:
            explanation_lines.append(f"Review Priority Bucket: {review_bucket.value}")
            
        # Optional: Calculate queue_rank based on score (simplified for single-run context)
        # In a real system, this might involve DB querying across the seller's queue.
        queue_rank = int(score * 10) # Simple relative integer score proxy
        
        return ListingDecisionResult(
            ranking_decision_id=decision_id,
            candidate_id=input_data.candidate_id,
            seller_account_id=input_data.seller_account_id,
            environment=input_data.environment,
            ranking_score=score,
            decision_class=decision,
            decision_reason=decision_reason,
            queue_type=queue_type,
            queue_rank=queue_rank,
            launch_priority_bucket=launch_bucket,
            review_priority_bucket=review_bucket,
            execution_blocked=is_blocked,
            block_reasons=block_reasons,
            recheck_required=is_stale,
            stale_flag=is_stale,
            explanation_lines=explanation_lines,
            ranking_components=components,
            created_at=now,
            updated_at=now
        )
