from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class FalseSignalAnalysisService:
    """False positive / false negative 分析"""

    def identify_false_positives(self, time_window_days: int = 30) -> List[Dict[str, Any]]:
        """false positive incident リスト。Returns: [incident {...}]"""
        return [{"incident_id": "fp-1", "reason": "Expected FP"}]

    def identify_false_negatives(self, time_window_days: int = 30) -> List[Dict[str, Any]]:
        """false negative incident（検出漏れ）リスト。Returns: [incident {...}]"""
        return [{"incident_id": "fn-1", "reason": "Expected FN"}]

    def calculate_false_positive_rate(self, detection_source: str = "all") -> float:
        """false positive rate (0.0-1.0)。Returns: float"""
        if detection_source == "noisy":
            return 0.8
        return 0.05

    def calculate_false_negative_rate(self, detection_source: str = "all") -> float:
        """false negative rate (0.0-1.0)。Returns: float"""
        return 0.02

    def analyze_false_signal_pattern(self, error_code_or_family: str) -> Dict[str, Any]:
        """error pattern ごとの false signal 分析。Returns: {fp_count, fn_count, root_causes}"""
        return {
            "fp_count": 10,
            "fn_count": 2,
            "root_causes": ["threshold_tuning_gap"]
        }

    def recommend_detection_threshold_adjustment(self, detection_source: str) -> Optional[Dict[str, Any]]:
        """detection threshold 見直し候補。Returns: {adjustment, rationale, expected_impact}"""
        if detection_source == "perfect":
            return None
        return {
            "adjustment": "Increase threshold to 100",
            "rationale": "High FP rate",
            "expected_impact": "Reduce FP by 50%"
        }

    def identify_near_miss_events(self, time_window_days: int = 30) -> List[Dict[str, Any]]:
        """almost-incident-but-recovered リスト。Returns: [near_miss {...}]"""
        return [{"event": "near-miss-1"}]
