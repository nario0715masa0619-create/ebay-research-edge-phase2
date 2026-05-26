import pytest
import datetime
from uuid import uuid4
from src.learning.repositories.learning_recommendation_repository_db import LearningRecommendationRepository
from src.learning.models.learning_recommendation import LearningRecommendation, RecommendationStatus, RecommendationType

@pytest.fixture
def repo():
    return LearningRecommendationRepository()

def create_dummy_rec() -> LearningRecommendation:
    return LearningRecommendation(
        recommendation_id=uuid4(),
        learning_record_id=uuid4(),
        recommendation_type=RecommendationType.ADJUST_INCIDENT_THRESHOLD,
        target_phase="N",
        target_scope="S",
        proposal_summary="S",
        proposal_details="D",
        priority=50,
        recommendation_status=RecommendationStatus.PROPOSED,
        review_due_at=datetime.datetime.utcnow(),
        approved_by=None,
        implemented_in_phase=None,
        implemented_commit_ref=None,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )

def test_create_recommendation(repo):
    r = create_dummy_rec()
    res = repo.create_recommendation(r)
    assert res.recommendation_id == r.recommendation_id
    assert repo.get_recommendation_by_id(r.recommendation_id) is not None

def test_get_recommendation_by_id_found(repo):
    r = create_dummy_rec()
    repo.create_recommendation(r)
    assert repo.get_recommendation_by_id(r.recommendation_id) == r

def test_update_recommendation(repo):
    r = create_dummy_rec()
    repo.create_recommendation(r)
    r.recommendation_status = RecommendationStatus.APPROVED
    res = repo.update_recommendation(r)
    assert res.recommendation_status == RecommendationStatus.APPROVED

def test_list_recommendations_filter_by_status(repo):
    r1 = create_dummy_rec()
    r2 = create_dummy_rec()
    r2.recommendation_status = RecommendationStatus.APPROVED
    repo.create_recommendation(r1)
    repo.create_recommendation(r2)
    recs, total = repo.list_recommendations(status=RecommendationStatus.APPROVED)
    assert total == 1
    assert recs[0].recommendation_status == RecommendationStatus.APPROVED

def test_list_recommendations_filter_by_target_phase(repo):
    r1 = create_dummy_rec()
    r1.target_phase = "Phase X"
    repo.create_recommendation(r1)
    recs, total = repo.list_recommendations(target_phase="Phase X")
    assert total == 1

def test_get_by_learning_record(repo):
    lid = uuid4()
    r1 = create_dummy_rec()
    r1.learning_record_id = lid
    repo.create_recommendation(r1)
    res = repo.get_recommendations_by_learning_record(lid)
    assert len(res) == 1

def test_get_pending_approvals(repo):
    r1 = create_dummy_rec()
    r1.recommendation_status = RecommendationStatus.PROPOSED
    r1.review_due_at = datetime.datetime.utcnow() - datetime.timedelta(days=2)
    repo.create_recommendation(r1)
    res = repo.get_pending_approvals()
    assert len(res) == 1

def test_count_by_status(repo):
    r1 = create_dummy_rec()
    r1.recommendation_status = RecommendationStatus.APPROVED
    repo.create_recommendation(r1)
    counts = repo.count_recommendations_by_status()
    assert counts[RecommendationStatus.APPROVED] == 1
