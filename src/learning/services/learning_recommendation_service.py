from typing import Optional, List, Tuple, Dict
from uuid import UUID, uuid4
from datetime import datetime

from src.learning.models.learning_recommendation import LearningRecommendation, RecommendationType, RecommendationStatus

class LearningRecommendationService:
    """Learning recommendation 管理"""

    def __init__(self):
        self.recommendations: Dict[UUID, LearningRecommendation] = {}

    def create_recommendation(
        self, 
        learning_record_id: UUID, 
        rec_type: RecommendationType, 
        target_phase: str, 
        target_scope: str, 
        proposal_summary: str, 
        proposal_details: str, 
        priority: int, 
        review_due_at: datetime, 
        created_by: str
    ) -> LearningRecommendation:
        """新規 recommendation 作成（status=PROPOSED）。Returns: LearningRecommendation"""
        rec = LearningRecommendation(
            recommendation_id=uuid4(),
            learning_record_id=learning_record_id,
            recommendation_type=rec_type,
            target_phase=target_phase,
            target_scope=target_scope,
            proposal_summary=proposal_summary,
            proposal_details=proposal_details,
            priority=priority,
            recommendation_status=RecommendationStatus.PROPOSED,
            review_due_at=review_due_at,
            approved_by=None,
            implemented_in_phase=None,
            implemented_commit_ref=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.recommendations[rec.recommendation_id] = rec
        return rec

    def list_recommendations(
        self, 
        status: Optional[RecommendationStatus] = None, 
        target_phase: Optional[str] = None, 
        priority_min: int = 0, 
        limit: int = 50, 
        offset: int = 0
    ) -> Tuple[List[LearningRecommendation], int]:
        """フィルタ + ページネーション。Returns: ([recommendations], total)"""
        filtered = list(self.recommendations.values())
        if status:
            filtered = [r for r in filtered if r.recommendation_status == status]
        if target_phase:
            filtered = [r for r in filtered if r.target_phase == target_phase]
        if priority_min > 0:
            filtered = [r for r in filtered if r.priority >= priority_min]
            
        filtered.sort(key=lambda x: x.priority, reverse=True)
        return filtered[offset:offset+limit], len(filtered)

    def get_recommendation_by_id(self, recommendation_id: UUID) -> Optional[LearningRecommendation]:
        """ID で取得。Returns: LearningRecommendation or None"""
        return self.recommendations.get(recommendation_id)

    def review_recommendation(self, recommendation_id: UUID, reviewer_id: str) -> LearningRecommendation:
        """status=UNDER_REVIEW。Returns: 更新済み recommendation"""
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        rec.recommendation_status = RecommendationStatus.UNDER_REVIEW
        rec.updated_at = datetime.utcnow()
        return rec

    def approve_recommendation(self, recommendation_id: UUID, approved_by: str) -> LearningRecommendation:
        """status=APPROVED。Returns: 更新済み recommendation"""
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        rec.recommendation_status = RecommendationStatus.APPROVED
        rec.approved_by = approved_by
        rec.updated_at = datetime.utcnow()
        return rec

    def reject_recommendation(self, recommendation_id: UUID, reason: str) -> LearningRecommendation:
        """status=REJECTED。Returns: 更新済み recommendation"""
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        rec.recommendation_status = RecommendationStatus.REJECTED
        rec.updated_at = datetime.utcnow()
        return rec

    def mark_implemented(self, recommendation_id: UUID, phase: str, commit_ref: str) -> LearningRecommendation:
        """status=IMPLEMENTED, implemented_in_phase, implemented_commit_ref セット。Returns: 更新済み recommendation"""
        rec = self.recommendations.get(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        rec.recommendation_status = RecommendationStatus.IMPLEMENTED
        rec.implemented_in_phase = phase
        rec.implemented_commit_ref = commit_ref
        rec.updated_at = datetime.utcnow()
        return rec
