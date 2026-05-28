from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from uuid import UUID
from dataclasses import dataclass

from src.learning.models.learning_record import LearningRecord, RootCauseCategory, LearningRecordStatus
from src.learning.models.learning_recommendation import LearningRecommendation

@dataclass
class RecurringIssueCluster:
    cluster_id: str
    root_cause_category: RootCauseCategory
    primary_seller: Optional[str]
    primary_environment: Optional[str]
    occurrence_count: int
    time_span_days: int
    most_recent_at: datetime
    affected_error_families: List[str]
    affected_sellers: int
    affected_environments: int

@dataclass
class FalseSignalSummary:
    false_positive_count: int
    false_positive_rate: float
    false_negative_count: int
    false_negative_rate: float
    by_detection_source: Dict[str, Dict[str, float]]
    top_false_positive_patterns: List[Tuple[str, int]]
    top_false_negative_patterns: List[Tuple[str, int]]

@dataclass
class LearningSummary:
    total_learning_records: int
    by_status: Dict[LearningRecordStatus, int]
    by_category: Dict[RootCauseCategory, int]
    false_positive_summary: FalseSignalSummary
    recurring_clusters_count: int
    pending_recommendations_count: int
    high_priority_recommendations: List[LearningRecommendation]


class LearningDashboardService:
    """Learning dashboard & summary"""

    def get_learning_summary(self, time_window_days: int = 30) -> Dict[str, Any]:
        """learning overview。Returns: {total_records, by_category, by_status, false_positive_count, recurring_clusters}"""
        return {
            "total_records": 100,
            "by_category": {RootCauseCategory.ENVIRONMENT_INSTABILITY: 50},
            "by_status": {LearningRecordStatus.OPEN: 10},
            "false_positive_count": 5,
            "recurring_clusters": 2
        }

    def get_top_root_causes(self, limit: int = 10) -> List[Tuple[RootCauseCategory, int]]:
        """最頻出 root cause。Returns: [(category, count)]"""
        return [(RootCauseCategory.ENVIRONMENT_INSTABILITY, 50)]

    def get_recurring_issue_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """recurring issue top-N。Returns: [cluster {...}]"""
        return [{"cluster_id": "c1", "count": 10}]

    def get_false_signal_summary(self) -> Dict[str, Any]:
        """false positive / false negative stats。Returns: {fp_rate, fn_rate, by_source}"""
        return {
            "fp_rate": 0.05,
            "fn_rate": 0.01,
            "by_source": {"all": {"fp_rate": 0.05}}
        }

    def get_seller_learning_profile(self, seller_account_id: str) -> Dict[str, Any]:
        """seller 別 learning profile。Returns: {recurring_issues, false_signals, recommended_actions}"""
        return {
            "recurring_issues": [],
            "false_signals": [],
            "recommended_actions": []
        }

    def get_environment_learning_profile(self, environment: str) -> Dict[str, Any]:
        """environment 別 learning profile。Returns: {recurring_issues, weak_points, recommendations}"""
        return {
            "recurring_issues": [],
            "weak_points": [],
            "recommendations": []
        }

    def get_recommendation_queue(self, limit: int = 20) -> List[LearningRecommendation]:
        """未レビュー recommendation リスト。Returns: [recommendation]"""
        return []

    def get_stale_learning_backlog(self, days_old: int = 14) -> List[LearningRecord]:
        """OPEN / UNDER_ANALYSIS で一定期間経った record。Returns: [learning_record]"""
        return []
