import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from src.learning.services.learning_recommendation_service import LearningRecommendationService
from src.learning.models.learning_recommendation import RecommendationType, RecommendationStatus

@pytest.fixture
def service():
    return LearningRecommendationService()

def test_create_recommendation(service):
    rec = service.create_recommendation(
        uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "Phase N", "scope", "Sum", "Det", 50, datetime.utcnow(), "u1"
    )
    assert rec.recommendation_status == RecommendationStatus.PROPOSED
    assert rec.priority == 50

def test_list_recommendations_filter_by_status(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    service.review_recommendation(r1.recommendation_id, "u2")
    
    recs, total = service.list_recommendations(status=RecommendationStatus.UNDER_REVIEW)
    assert total == 1
    assert recs[0].recommendation_id == r1.recommendation_id

def test_list_recommendations_filter_by_phase(service):
    service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "Phase N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    recs, total = service.list_recommendations(target_phase="Phase N")
    assert total == 1

def test_get_recommendation_by_id(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    assert service.get_recommendation_by_id(r1.recommendation_id) is not None
    assert service.get_recommendation_by_id(uuid4()) is None

def test_review_recommendation(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    updated = service.review_recommendation(r1.recommendation_id, "u2")
    assert updated.recommendation_status == RecommendationStatus.UNDER_REVIEW

def test_approve_recommendation(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    updated = service.approve_recommendation(r1.recommendation_id, "u2")
    assert updated.recommendation_status == RecommendationStatus.APPROVED
    assert updated.approved_by == "u2"

def test_reject_recommendation(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    updated = service.reject_recommendation(r1.recommendation_id, "bad")
    assert updated.recommendation_status == RecommendationStatus.REJECTED

def test_mark_implemented(service):
    r1 = service.create_recommendation(uuid4(), RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    updated = service.mark_implemented(r1.recommendation_id, "Phase N", "abc1234")
    assert updated.recommendation_status == RecommendationStatus.IMPLEMENTED
    assert updated.implemented_in_phase == "Phase N"
    assert updated.implemented_commit_ref == "abc1234"
