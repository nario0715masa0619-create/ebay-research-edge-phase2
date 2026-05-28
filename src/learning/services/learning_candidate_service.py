from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from src.learning.models.learning_candidate import LearningCandidate, CandidateSource
from src.learning.models.learning_record import RootCauseCategory, ImpactScope

class LearningCandidateService:
    """Learning candidate 検出・生成"""

    def __init__(self):
        self.candidates: List[LearningCandidate] = []

    def generate_candidate_from_resolved_incident(self, incident_id: UUID) -> Optional[LearningCandidate]:
        """resolved/closed incident → candidate 生成。Returns: LearningCandidate or None"""
        candidate = LearningCandidate(
            candidate_id=uuid4(),
            candidate_source=CandidateSource.RESOLVED_INCIDENT,
            title=f"Incident {incident_id} Review",
            summary="Review resolved incident for learning opportunities.",
            suggested_root_cause_category=RootCauseCategory.UNKNOWN_PENDING_ANALYSIS,
            suggested_impact_scope=ImpactScope.GLOBAL,
            seller_account_id=None,
            environment=None,
            linked_incident_id=incident_id,
            linked_policy_id=None,
            confidence_score=0.8,
            created_at=datetime.utcnow()
        )
        self.candidates.append(candidate)
        return candidate

    def generate_candidates_from_incidents(self, incident_ids: List[UUID]) -> List[LearningCandidate]:
        """複数 incident → candidates。Returns: [LearningCandidate]"""
        res = []
        for iid in incident_ids:
            c = self.generate_candidate_from_resolved_incident(iid)
            if c:
                res.append(c)
        return res

    def detect_repeated_pattern(self, root_cause_category: RootCauseCategory, seller_account_id: Optional[str] = None, environment: Optional[str] = None, time_window_hours: int = 24) -> Optional[LearningCandidate]:
        """同一原因の繰り返しを検出。Returns: LearningCandidate or None"""
        candidate = LearningCandidate(
            candidate_id=uuid4(),
            candidate_source=CandidateSource.REPEATED_PATTERN,
            title=f"Repeated {root_cause_category.value} pattern detected",
            summary=f"Detected multiple issues related to {root_cause_category.value}",
            suggested_root_cause_category=root_cause_category,
            suggested_impact_scope=ImpactScope.SELLER if seller_account_id else ImpactScope.ENVIRONMENT if environment else ImpactScope.GLOBAL,
            seller_account_id=seller_account_id,
            environment=environment,
            linked_incident_id=None,
            linked_policy_id=None,
            confidence_score=0.9,
            created_at=datetime.utcnow()
        )
        self.candidates.append(candidate)
        return candidate

    def detect_false_positive_cluster(self, incident_type_or_error_family: str, time_window_hours: int = 24) -> Optional[LearningCandidate]:
        """false positive pattern 検出。Returns: LearningCandidate or None"""
        candidate = LearningCandidate(
            candidate_id=uuid4(),
            candidate_source=CandidateSource.FALSE_POSITIVE_DETECTED,
            title=f"False Positive Cluster: {incident_type_or_error_family}",
            summary="High rate of false positives detected.",
            suggested_root_cause_category=RootCauseCategory.DETECTION_FALSE_POSITIVE,
            suggested_impact_scope=ImpactScope.GLOBAL,
            seller_account_id=None,
            environment=None,
            linked_incident_id=None,
            linked_policy_id=None,
            confidence_score=0.85,
            created_at=datetime.utcnow()
        )
        self.candidates.append(candidate)
        return candidate

    def detect_recurring_error_family(self, error_code_family: str) -> Optional[LearningCandidate]:
        """error family recurring 検出。Returns: LearningCandidate or None"""
        candidate = LearningCandidate(
            candidate_id=uuid4(),
            candidate_source=CandidateSource.RECURRING_ERROR_FAMILY,
            title=f"Recurring Error Family: {error_code_family}",
            summary=f"Error family {error_code_family} is recurring frequently.",
            suggested_root_cause_category=RootCauseCategory.UNKNOWN_PENDING_ANALYSIS,
            suggested_impact_scope=ImpactScope.GLOBAL,
            seller_account_id=None,
            environment=None,
            linked_incident_id=None,
            linked_policy_id=None,
            confidence_score=0.75,
            created_at=datetime.utcnow()
        )
        self.candidates.append(candidate)
        return candidate

    def detect_policy_ineffectiveness(self, policy_id: UUID) -> Optional[LearningCandidate]:
        """policy 適用後も failure 続く。Returns: LearningCandidate or None"""
        candidate = LearningCandidate(
            candidate_id=uuid4(),
            candidate_source=CandidateSource.POLICY_INEFFECTIVE,
            title=f"Ineffective Policy {policy_id}",
            summary="Failures continued after policy application.",
            suggested_root_cause_category=RootCauseCategory.POLICY_MISCONFIGURATION,
            suggested_impact_scope=ImpactScope.GLOBAL,
            seller_account_id=None,
            environment=None,
            linked_incident_id=None,
            linked_policy_id=policy_id,
            confidence_score=0.95,
            created_at=datetime.utcnow()
        )
        self.candidates.append(candidate)
        return candidate

    def scan_all_candidates(self, limit: int = 50) -> List[LearningCandidate]:
        """全 candidate scan（incident + pattern + error family）。Returns: [LearningCandidate]"""
        return sorted(self.candidates, key=lambda c: self.assess_candidate_priority(c), reverse=True)[:limit]

    def assess_candidate_priority(self, candidate: LearningCandidate) -> int:
        """priority スコア計算 (1-100)。Returns: int"""
        score = int(candidate.confidence_score * 100)
        if candidate.candidate_source == CandidateSource.POLICY_INEFFECTIVE:
            score += 10
        elif candidate.candidate_source == CandidateSource.FALSE_POSITIVE_DETECTED:
            score += 5
        return min(100, max(1, score))
