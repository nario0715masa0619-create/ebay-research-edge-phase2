from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
import logging

from src.ops_policy.services.incident_detection_service import IncidentDetectionService
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.models.enums import PolicyStatus

logger = logging.getLogger(__name__)

class PolicyCandidateScanJob:
    def __init__(self, detection_service: IncidentDetectionService):
        self.detection_service = detection_service

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Scan incidents/alerts for policy candidates.
        Returns: {job_id, status, candidates_count, top_candidates, executed_at}
        """
        job_id = str(uuid.uuid4())
        
        candidates = self.detection_service.scan_all_candidates()
        top_candidates = [
            str(c.candidate_id) for c in candidates 
            if c.severity and c.severity.name in ('CRITICAL', 'HIGH')
        ][:5]
        
        if not dry_run:
            # Output to log (manual review needed)
            logger.info(f"Scan complete. Found {len(candidates)} candidates.")
            
        return {
            "job_id": job_id,
            "status": "success",
            "candidates_count": len(candidates),
            "top_candidates": top_candidates,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

class PolicyExpiryJob:
    def __init__(self, management_service: OpsPolicyManagementService):
        self.management_service = management_service

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Check & expire policies past effective_until.
        Returns: {job_id, status, expired_count, expired_policies, executed_at}
        """
        job_id = str(uuid.uuid4())
        expired_ids = []
        
        policies, _ = self.management_service.list_policies(status=PolicyStatus.ACTIVE)
        now = datetime.now(timezone.utc).replace(tzinfo=None) # Keep naive if models are naive
        
        for policy in policies:
            if policy.effective_until and policy.effective_until < now:
                if not dry_run:
                    # In real code, transition status
                    try:
                        # Assuming state_machine validation would pass
                        policy.status = PolicyStatus.EXPIRED
                        policy.is_expired = True
                        # Would call self.management_service.add_policy_note and repo update
                        expired_ids.append(str(policy.policy_id))
                    except Exception as e:
                        logger.error(f"Failed to expire {policy.policy_id}: {e}")
                else:
                    expired_ids.append(str(policy.policy_id))

        return {
            "job_id": job_id,
            "status": "success",
            "expired_count": len(expired_ids),
            "expired_policies": expired_ids,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

class PolicyReviewDueScanJob:
    def __init__(self, management_service: OpsPolicyManagementService):
        self.management_service = management_service

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Scan policies with review_due_at in past, status=APPROVED.
        Returns: {job_id, status, overdue_count, overdue_policies, executed_at}
        """
        job_id = str(uuid.uuid4())
        overdue_ids = []
        
        policies, _ = self.management_service.list_policies(status=PolicyStatus.APPROVED)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for policy in policies:
            if policy.review_due_at and policy.review_due_at < now:
                overdue_ids.append(str(policy.policy_id))
                if not dry_run:
                    logger.warning(f"Policy {policy.policy_id} is overdue for review!")

        return {
            "job_id": job_id,
            "status": "success",
            "overdue_count": len(overdue_ids),
            "overdue_policies": overdue_ids,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
