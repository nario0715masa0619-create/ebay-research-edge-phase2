import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.orchestrator.policy_jobs import PolicyCandidateScanJob, PolicyExpiryJob, PolicyReviewDueScanJob
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.services.incident_detection_service import IncidentDetectionService
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus
from src.ops_policy.models.ops_policy import OpsPolicy

@pytest.fixture
def management_service():
    svc = OpsPolicyManagementService()
    svc.policies.clear()
    svc.events.clear()
    return svc

@pytest.fixture
def detection_service():
    return IncidentDetectionService()

from unittest.mock import MagicMock
from src.ops_policy.models.ops_policy_candidate import OpsPolicyCandidate
from src.ops_policy.models.enums import Severity

def test_candidate_scan_job(detection_service):
    job = PolicyCandidateScanJob(detection_service)
    
    dummy_candidate = OpsPolicyCandidate(
        candidate_id=uuid4(),
        candidate_type=None,
        target_scope=None,
        target_id=None,
        severity=Severity.CRITICAL,
        confidence_score=0.9,
        recommended_action_type=None,
        reason_summary="Test",
        linked_incident_id=None,
        created_at=datetime.utcnow()
    )
    job.detection_service.scan_all_candidates = MagicMock(return_value=[dummy_candidate])
    
    # Run once
    res1 = job.execute()
    assert res1["status"] == "success"
    assert res1["candidates_count"] > 0
    
    # Run again (idempotent)
    res2 = job.execute()
    assert res1["candidates_count"] == res2["candidates_count"]

def test_expiry_job(management_service):
    # Setup policies
    p1 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    p1.effective_until = datetime.utcnow() - timedelta(days=1) # Expired
    
    p2 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p2.status = PolicyStatus.ACTIVE
    p2.effective_until = datetime.utcnow() + timedelta(days=1) # Not expired
    
    job = PolicyExpiryJob(management_service)
    
    # Run first time
    res = job.execute(dry_run=False)
    assert res["expired_count"] == 1
    assert str(p1.policy_id) in res["expired_policies"]
    assert p1.status == PolicyStatus.EXPIRED
    
    # Run second time (idempotent)
    res2 = job.execute(dry_run=False)
    assert res2["expired_count"] == 0

def test_expiry_job_dry_run(management_service):
    p1 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    p1.effective_until = datetime.utcnow() - timedelta(days=1) # Expired
    
    job = PolicyExpiryJob(management_service)
    res = job.execute(dry_run=True)
    assert res["expired_count"] == 1
    assert p1.status == PolicyStatus.ACTIVE # Unchanged because dry_run

def test_review_due_scan_job(management_service):
    p1 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.APPROVED
    p1.review_due_at = datetime.utcnow() - timedelta(days=1) # Overdue
    
    p2 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p2.status = PolicyStatus.APPROVED
    p2.review_due_at = datetime.utcnow() + timedelta(days=1) # Not overdue
    
    job = PolicyReviewDueScanJob(management_service)
    
    # Run first time
    res = job.execute(dry_run=False)
    assert res["overdue_count"] == 1
    assert str(p1.policy_id) in res["overdue_policies"]
    
    # Run again (idempotent, it just reads)
    res2 = job.execute(dry_run=False)
    assert res2["overdue_count"] == 1

def test_review_due_scan_job_dry_run(management_service):
    p1 = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.APPROVED
    p1.review_due_at = datetime.utcnow() - timedelta(days=1) # Overdue
    
    job = PolicyReviewDueScanJob(management_service)
    res = job.execute(dry_run=True)
    assert res["overdue_count"] == 1
