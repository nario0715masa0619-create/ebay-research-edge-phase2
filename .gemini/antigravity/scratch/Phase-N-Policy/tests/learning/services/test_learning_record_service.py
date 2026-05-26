import pytest
from uuid import uuid4
from src.learning.services.learning_record_service import LearningRecordService
from src.learning.models.learning_record import (
    RootCauseCategory, ImpactScope, LearningRecordStatus, EffectivenessRating, ConfidenceLevel
)

@pytest.fixture
def service():
    return LearningRecordService()

def test_create_learning_record(service):
    rec = service.create_learning_record("Test", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    assert rec.title == "Test"
    assert rec.status == LearningRecordStatus.OPEN
    assert rec.learning_record_id in service.records

def test_get_learning_record_by_id_found(service):
    rec = service.create_learning_record("Test", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    found = service.get_learning_record_by_id(rec.learning_record_id)
    assert found is not None
    assert found.learning_record_id == rec.learning_record_id

def test_get_learning_record_by_id_not_found(service):
    assert service.get_learning_record_by_id(uuid4()) is None

def test_list_learning_records_all(service):
    service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    service.create_learning_record("Test2", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    recs, total = service.list_learning_records()
    assert total == 2
    assert len(recs) == 2

def test_list_learning_records_filter_by_status(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    r2 = service.create_learning_record("Test2", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    service.close_learning_record(r1.learning_record_id)
    
    recs, total = service.list_learning_records(status=LearningRecordStatus.CLOSED)
    assert total == 1
    assert recs[0].learning_record_id == r1.learning_record_id

def test_list_learning_records_filter_by_category(service):
    service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    service.create_learning_record("Test2", "Sum", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    
    recs, total = service.list_learning_records(category=RootCauseCategory.POLICY_MISCONFIGURATION)
    assert total == 1
    assert recs[0].root_cause_category == RootCauseCategory.POLICY_MISCONFIGURATION

def test_list_learning_records_filter_by_seller(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    r1.seller_account_id = "s1"
    
    r2 = service.create_learning_record("Test2", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    r2.seller_account_id = "s2"
    
    recs, total = service.list_learning_records(seller_account_id="s1")
    assert total == 1
    assert recs[0].seller_account_id == "s1"

def test_list_learning_records_pagination(service):
    for i in range(5):
        service.create_learning_record(f"Test{i}", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
        
    recs, total = service.list_learning_records(limit=2, offset=0)
    assert total == 5
    assert len(recs) == 2

def test_update_learning_record_title_summary(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    updated = service.update_learning_record(r1.learning_record_id, title="New Title", summary="New Sum")
    assert updated.title == "New Title"
    assert updated.summary == "New Sum"

def test_update_learning_record_effectiveness(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    updated = service.update_learning_record(r1.learning_record_id, effectiveness=EffectivenessRating.HIGHLY_EFFECTIVE)
    assert updated.effectiveness_rating == EffectivenessRating.HIGHLY_EFFECTIVE

def test_close_learning_record(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    updated = service.close_learning_record(r1.learning_record_id)
    assert updated.status == LearningRecordStatus.CLOSED
    assert updated.closed_at is not None

def test_link_incident(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    iid = uuid4()
    updated = service.link_incident(r1.learning_record_id, iid)
    assert updated.linked_incident_id == iid

def test_link_policy(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    pid = uuid4()
    updated = service.link_policy(r1.learning_record_id, pid)
    assert updated.linked_policy_id == pid

def test_count_records_by_category(service):
    service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    service.create_learning_record("Test2", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    service.create_learning_record("Test3", "Sum", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    
    counts = service.count_records_by_category()
    assert counts[RootCauseCategory.DETECTION_FALSE_POSITIVE] == 2
    assert counts[RootCauseCategory.POLICY_MISCONFIGURATION] == 1

def test_linked_records_immutable_created_at(service):
    r1 = service.create_learning_record("Test1", "Sum", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    orig_created = r1.created_at
    updated = service.update_learning_record(r1.learning_record_id, title="New Title")
    assert updated.created_at == orig_created
