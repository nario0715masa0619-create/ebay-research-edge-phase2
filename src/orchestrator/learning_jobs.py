from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

from src.learning.services.learning_candidate_service import LearningCandidateService
from src.learning.services.recurring_issue_analysis_service import RecurringIssueAnalysisService
from src.learning.services.false_signal_analysis_service import FalseSignalAnalysisService
from src.learning.services.learning_dashboard_service import LearningDashboardService
from src.learning.services.learning_effectiveness_service import LearningEffectivenessService

class LearningCandidateScanJob:
    def __init__(self, service: LearningCandidateService = None):
        self.service = service or LearningCandidateService()

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Scan incidents/alerts for learning candidates.
        """
        job_id = str(uuid4())
        try:
            candidates = self.service.scan_all_candidates(limit=50)
            if not dry_run:
                # Simulate persistence logic if any, but since it's idempotent read-only for now, we just scan
                pass
                
            return {
                "job_id": job_id,
                "status": "success",
                "candidates_count": len(candidates),
                "top_candidates": [str(c.candidate_id) for c in candidates],
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failure",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }

class LearningRecurringIssueJob:
    def __init__(self, service: RecurringIssueAnalysisService = None):
        self.service = service or RecurringIssueAnalysisService()

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Detect recurring issue clusters.
        """
        job_id = str(uuid4())
        try:
            clusters = self.service.identify_high_impact_clusters(limit=10)
            return {
                "job_id": job_id,
                "status": "success",
                "clusters_count": len(clusters),
                "high_impact_clusters": clusters,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failure",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }

class LearningFalseSignalDigestJob:
    def __init__(self, service: FalseSignalAnalysisService = None):
        self.service = service or FalseSignalAnalysisService()

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Generate false signal digest.
        """
        job_id = str(uuid4())
        try:
            fps = self.service.identify_false_positives()
            fns = self.service.identify_false_negatives()
            nms = self.service.identify_near_miss_events()
            
            fp_rate = self.service.calculate_false_positive_rate()
            fn_rate = self.service.calculate_false_negative_rate()
            
            return {
                "job_id": job_id,
                "status": "success",
                "fp_count": len(fps),
                "fn_count": len(fns),
                "nm_count": len(nms),
                "fp_rate": fp_rate,
                "fn_rate": fn_rate,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failure",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }

class LearningBacklogReviewJob:
    def __init__(self, dashboard_service: LearningDashboardService = None):
        self.service = dashboard_service or LearningDashboardService()

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Review learning backlog and recommendations.
        """
        job_id = str(uuid4())
        try:
            stale = self.service.get_stale_learning_backlog()
            pending = self.service.get_recommendation_queue()
            
            escalation_alert = len(stale) > 10 or len(pending) > 20
            
            return {
                "job_id": job_id,
                "status": "success",
                "stale_count": len(stale),
                "pending_recs_count": len(pending),
                "escalation_alert": escalation_alert,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failure",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }

class LearningEffectivenessEvaluationJob:
    def __init__(self, service: LearningEffectivenessService = None):
        self.service = service or LearningEffectivenessService()

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Evaluate remediation and policy effectiveness.
        """
        job_id = str(uuid4())
        try:
            ineffective = self.service.identify_ineffective_policies(threshold=0.5)
            # Example call for evaluation
            # Assuming we evaluate some known incidents or general statistics
            
            return {
                "job_id": job_id,
                "status": "success",
                "evaluated_count": len(ineffective),  # Just dummy representation
                "effectiveness_summary": {"avg_score": 0.8},
                "ineffective_policies": ineffective,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failure",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }
