from typing import Dict, Any, Tuple

class RetryClassifier:
    def classify(self, error_res: Dict[str, Any]) -> Tuple[str, bool, bool]:
        """
        Returns (classification, retryable_flag, review_required_flag)
        """
        error_msg = str(error_res.get("error", "")).lower()
        
        # Section 14: RetryClassifier 設計
        
        # retryable
        retryable_keywords = ["timeout", "network", "temporary", "500", "503"]
        if any(k in error_msg for k in retryable_keywords):
            return "retryable", True, False
            
        # review_required
        review_keywords = ["policy", "location", "aspect", "category", "condition", "duplicate"]
        if any(k in error_msg for k in review_keywords):
            return "review_required", False, True
            
        # fatal (default)
        return "fatal", False, False
