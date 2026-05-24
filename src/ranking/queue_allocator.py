from typing import Tuple, Optional
from src.ranking.models import RankingInput, DecisionClass, QueueType, LaunchPriorityBucket, ReviewPriorityBucket
from src.ranking.config import RankingSettings

class QueueAllocator:
    def __init__(self, settings: RankingSettings):
        self.settings = settings
        
    def allocate(self, decision: DecisionClass, score: float, is_blocked: bool, is_stale: bool, input_data: RankingInput) -> Tuple[QueueType, Optional[LaunchPriorityBucket], Optional[ReviewPriorityBucket]]:
        queue_type = QueueType.REJECT_ARCHIVE
        launch_bucket = None
        review_bucket = None
        
        if decision == DecisionClass.AUTO_LAUNCH:
            queue_type = QueueType.AUTO_LAUNCH_QUEUE
            if score >= 90:
                launch_bucket = LaunchPriorityBucket.URGENT
            elif score >= 80:
                launch_bucket = LaunchPriorityBucket.HIGH
            else:
                launch_bucket = LaunchPriorityBucket.NORMAL
                
            if is_blocked:
                # Safety fallback, though decision_engine shouldn't allow this
                queue_type = QueueType.WATCH_QUEUE
                launch_bucket = LaunchPriorityBucket.DEFERRED
                
        elif decision == DecisionClass.MANUAL_REVIEW:
            queue_type = QueueType.REVIEW_QUEUE
            # Simplified Hybrid priority: Expected Upside * Risk
            # High profit + High risk = Critical Review
            if input_data.confidence_adjusted_profit >= self.settings.auto_launch_min_profit and input_data.profitability_unsafe_reasons:
                review_bucket = ReviewPriorityBucket.CRITICAL_REVIEW
            elif score >= 70:
                review_bucket = ReviewPriorityBucket.HIGH_REVIEW
            elif score >= 50:
                review_bucket = ReviewPriorityBucket.NORMAL_REVIEW
            else:
                review_bucket = ReviewPriorityBucket.LOW_REVIEW
                
        elif decision == DecisionClass.WATCHLIST:
            queue_type = QueueType.WATCH_QUEUE
            if is_blocked:
                launch_bucket = LaunchPriorityBucket.DEFERRED
                
        elif decision == DecisionClass.REJECT:
            queue_type = QueueType.REJECT_ARCHIVE
            
        return queue_type, launch_bucket, review_bucket
