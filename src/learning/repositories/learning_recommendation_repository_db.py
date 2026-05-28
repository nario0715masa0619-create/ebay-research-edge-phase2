from typing import Optional, List, Tuple, Dict
from uuid import UUID
from datetime import datetime, timedelta
from src.learning.models.learning_recommendation import LearningRecommendation, RecommendationStatus

class LearningRecommendationRepository:
    """DB-backed recommendation repository"""
    def __init__(self):
        self.recs = {}

    def create_recommendation(self, rec: LearningRecommendation) -> LearningRecommendation:
        self.recs[rec.recommendation_id] = rec
        return rec

    def get_recommendation_by_id(self, recommendation_id: UUID) -> Optional[LearningRecommendation]:
        return self.recs.get(recommendation_id)

    def update_recommendation(self, rec: LearningRecommendation) -> LearningRecommendation:
        if rec.recommendation_id in self.recs:
            self.recs[rec.recommendation_id] = rec
        return rec

    def list_recommendations(
        self, 
        status: Optional[RecommendationStatus] = None, 
        target_phase: Optional[str] = None, 
        priority_min: int = 0, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[LearningRecommendation], int]:
        
        filtered = list(self.recs.values())
        if status:
            filtered = [r for r in filtered if r.recommendation_status == status]
        if target_phase:
            filtered = [r for r in filtered if r.target_phase == target_phase]
            
        filtered = [r for r in filtered if r.priority >= priority_min]
        
        total = len(filtered)
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[offset:offset+limit], total

    def get_recommendations_by_learning_record(self, learning_record_id: UUID) -> List[LearningRecommendation]:
        return [r for r in self.recs.values() if r.learning_record_id == learning_record_id]

    def get_recommendations_by_status(self, status: RecommendationStatus) -> List[LearningRecommendation]:
        return [r for r in self.recs.values() if r.recommendation_status == status]

    def get_pending_approvals(self, days_overdue: int = 0) -> List[LearningRecommendation]:
        cutoff = datetime.utcnow() - timedelta(days=days_overdue)
        return [
            r for r in self.recs.values() 
            if r.recommendation_status in [RecommendationStatus.PROPOSED, RecommendationStatus.UNDER_REVIEW]
            and r.review_due_at < cutoff
        ]

    def count_recommendations_by_status(self) -> Dict[RecommendationStatus, int]:
        counts = {}
        for r in self.recs.values():
            counts[r.recommendation_status] = counts.get(r.recommendation_status, 0) + 1
        return counts
