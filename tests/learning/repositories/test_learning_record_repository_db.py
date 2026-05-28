import pytest
from uuid import uuid4
from datetime import datetime
from src.learning.repositories.learning_record_repository_db import LearningRecordRepository
from src.learning.models.learning_record import LearningRecord, RootCauseCategory, ImpactScope, EffectivenessRating, ConfidenceLevel, LearningRecordStatus

@pytest.fixture
def repo():
    return LearningRecordRepository()

def create_dummy_record() -> LearningRecord:
    return LearningRecord(
        learning_record_id=uuid4(),
        title="T",
        summary="S",
        root_cause_category=RootCauseCategory.POLICY_MISCONFIGURATION,
        root_cause_subcategory=None,
        impact_scope=ImpactScope.GLOBAL,
        seller_account_id=None,
        environment=None,
        linked_incident_id=None,
        linked_policy_id=None,
        linked_report_id=None,
        is_false_positive=False,
        is_false_negative=False,
        is_near_miss=False,
        effectiveness_rating=EffectivenessRating.INEFFECTIVE,
        confidence_level=ConfidenceLevel.HIGH,
        recommended_action_type=None,
        recommended_change_scope=None,
        status=LearningRecordStatus.OPEN,
        created_by="u",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        closed_at=None,
        metadata_json={}
    )

def test_create_record(repo):
    r = create_dummy_record()
    res = repo.create_record(r)
    assert res.learning_record_id == r.learning_record_id
    assert repo.get_record_by_id(r.learning_record_id) is not None

def test_get_record_by_id_found(repo):
    r = create_dummy_record()
    repo.create_record(r)
    assert repo.get_record_by_id(r.learning_record_id) == r

def test_get_record_by_id_not_found(repo):
    assert repo.get_record_by_id(uuid4()) is None

def test_update_record(repo):
    r = create_dummy_record()
    repo.create_record(r)
    r.status = LearningRecordStatus.CLOSED
    res = repo.update_record(r)
    assert res.status == LearningRecordStatus.CLOSED
    assert repo.get_record_by_id(r.learning_record_id).status == LearningRecordStatus.CLOSED

def test_list_records_all(repo):
    repo.create_record(create_dummy_record())
    repo.create_record(create_dummy_record())
    recs, total = repo.list_records()
    assert total == 2
    assert len(recs) == 2

def test_list_records_filter_by_status(repo):
    r1 = create_dummy_record()
    r2 = create_dummy_record()
    r2.status = LearningRecordStatus.CLOSED
    repo.create_record(r1)
    repo.create_record(r2)
    recs, total = repo.list_records(status=LearningRecordStatus.CLOSED)
    assert total == 1
    assert recs[0].status == LearningRecordStatus.CLOSED

def test_list_records_filter_by_category(repo):
    r1 = create_dummy_record()
    r2 = create_dummy_record()
    r2.root_cause_category = RootCauseCategory.ENVIRONMENT_INSTABILITY
    repo.create_record(r1)
    repo.create_record(r2)
    recs, total = repo.list_records(category=RootCauseCategory.ENVIRONMENT_INSTABILITY)
    assert total == 1
    assert recs[0].root_cause_category == RootCauseCategory.ENVIRONMENT_INSTABILITY

def test_list_records_filter_by_seller(repo):
    r1 = create_dummy_record()
    r1.seller_account_id = "s1"
    repo.create_record(r1)
    recs, total = repo.list_records(seller_account_id="s1")
    assert total == 1

def test_list_records_filter_by_false_positive(repo):
    r1 = create_dummy_record()
    r1.is_false_positive = True
    repo.create_record(r1)
    recs, total = repo.list_records(false_positive=True)
    assert total == 1

def test_list_records_pagination(repo):
    for _ in range(5):
        repo.create_record(create_dummy_record())
    recs, total = repo.list_records(limit=2)
    assert total == 5
    assert len(recs) == 2

def test_get_records_by_category(repo):
    r1 = create_dummy_record()
    r1.root_cause_category = RootCauseCategory.DETECTION_FALSE_POSITIVE
    repo.create_record(r1)
    res = repo.get_records_by_category(RootCauseCategory.DETECTION_FALSE_POSITIVE)
    assert len(res) == 1

def test_get_records_by_seller(repo):
    r1 = create_dummy_record()
    r1.seller_account_id = "sell"
    repo.create_record(r1)
    res = repo.get_records_by_seller("sell")
    assert len(res) == 1

def test_count_by_status(repo):
    r1 = create_dummy_record()
    r1.status = LearningRecordStatus.CLOSED
    repo.create_record(r1)
    repo.create_record(create_dummy_record())
    counts = repo.count_records_by_status()
    assert counts[LearningRecordStatus.CLOSED] == 1
    assert counts[LearningRecordStatus.OPEN] == 1

def test_count_by_category(repo):
    r1 = create_dummy_record()
    repo.create_record(r1)
    counts = repo.count_records_by_category()
    assert counts[RootCauseCategory.POLICY_MISCONFIGURATION] == 1

def test_get_stale_records(repo):
    import datetime
    r1 = create_dummy_record()
    r1.created_at = datetime.datetime.utcnow() - datetime.timedelta(days=20)
    repo.create_record(r1)
    res = repo.get_stale_records()
    assert len(res) == 1
