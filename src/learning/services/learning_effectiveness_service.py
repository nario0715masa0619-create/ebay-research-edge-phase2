from typing import List, Tuple, Dict, Any
from uuid import UUID
from collections import defaultdict
import random

from src.learning.models.learning_record import EffectivenessRating, RootCauseCategory

class LearningEffectivenessService:
    """Remediation / Policy / RCA 有効性評価"""

    def evaluate_remediation_effectiveness(self, incident_id: UUID, policy_ids: List[UUID]) -> EffectivenessRating:
        """policy 適用後の incident resolution 評価。Returns: EffectivenessRating"""
        # 実際には incident status や recurrence を確認する
        # mock implementation
        return random.choice(list(EffectivenessRating))

    def calculate_effectiveness_score(self, incident_id: UUID, initial_severity: str, resolution_time_hours: float, recurrence_within_days: int) -> float:
        """effectiveness score 計算 (0.0-1.0)。Returns: float"""
        score = 1.0
        if initial_severity.lower() == "critical":
            score -= 0.1
        if resolution_time_hours > 24:
            score -= 0.3
        elif resolution_time_hours > 4:
            score -= 0.1
            
        if recurrence_within_days < 7:
            score -= 0.5
        elif recurrence_within_days < 30:
            score -= 0.2
            
        return max(0.0, min(1.0, score))

    def get_most_effective_remediation_types(self, root_cause_category: RootCauseCategory, limit: int = 5) -> List[Tuple[str, float]]:
        """cause 別最有効 remediation type ランキング。Returns: [(type, effectiveness_score)]"""
        # mock
        mock_data = [
            ("Adjust Threshold", 0.9),
            ("Add Exception", 0.8),
            ("Tighten Policy", 0.75),
            ("Manual Override", 0.6)
        ]
        return mock_data[:limit]

    def assess_policy_effectiveness_for_seller(self, seller_account_id: str, policy_id: UUID) -> Dict[str, Any]:
        """seller/policy 組み合わせの有効性分析。Returns: {effectiveness, recurring_count, avg_resolution_time}"""
        return {
            "effectiveness": 0.85,
            "recurring_count": 1,
            "avg_resolution_time": 2.5
        }

    def compare_remediation_approaches(self, incident_family: str) -> Dict[str, float]:
        """異なる remediation approach の比較。Returns: {approach: effectiveness_score}"""
        return {
            "automated_policy": 0.9,
            "manual_review": 0.6,
            "threshold_tuning": 0.8
        }

    def track_resolution_timeline(self, incident_id: UUID) -> List[Tuple[str, float]]:
        """incident から resolution までの段階別時間。Returns: [(stage, hours)]"""
        return [
            ("Detection", 0.1),
            ("Policy Application", 0.05),
            ("Effect Verification", 2.0),
            ("Resolution", 0.5)
        ]

    def identify_ineffective_policies(self, threshold: float = 0.4) -> List[UUID]:
        """effectiveness < threshold な policy ID リスト。Returns: [policy_id]"""
        return []
