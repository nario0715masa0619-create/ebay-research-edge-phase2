from typing import List, Optional
from src.discovery.review_models import ReviewQueueItem, CandidateCompareView

class ReviewQueueService:
    """
    Handles retrieving the list of candidates requiring review
    and assembling the detailed comparison view for a specific candidate.
    """
    
    def __init__(self, review_queue_repo):
        self.repo = review_queue_repo
        
    def get_pending_queue(self, limit: int = 50, offset: int = 0, sort_by: str = "ambiguity_desc") -> List[ReviewQueueItem]:
        """
        Fetch candidates where review_required = True.
        """
        return self.repo.get_pending_queue(limit=limit, offset=offset, sort_by=sort_by)
        
    def get_candidate_compare_view(self, candidate_id: str) -> Optional[CandidateCompareView]:
        """
        Fetch a detailed view of a candidate and its linked sources to assist human review.
        """
        return self.repo.get_candidate_compare_view(candidate_id)
