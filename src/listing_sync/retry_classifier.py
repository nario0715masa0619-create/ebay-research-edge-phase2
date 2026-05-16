from typing import Dict, Any, Tuple

class SyncRetryClassifier:
    def classify(self, error_res: Dict[str, Any]) -> Tuple[str, bool, bool]:
        """
        Classifies sync errors into retryable/review/fatal.
        Returns (classification, is_retryable, is_review)
        """
        error_code = error_res.get("error")
        status_code = error_res.get("status_code", 0)

        if status_code == 429 or status_code >= 500:
            return "retryable", True, False
        
        if status_code == 404:
            return "review_required", False, True
            
        if error_code in ["token_expired", "rate_limited"]:
            return "retryable", True, False

        return "fatal", False, True
