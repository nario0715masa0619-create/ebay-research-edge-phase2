import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.db.models import Base, ReportArtifactModel
from src.listing_execution.repositories.report_artifact_repository_db import ReportArtifactRepositoryDB

@pytest.fixture
def engine():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def repo(session):
    return ReportArtifactRepositoryDB(session)

def create_mock_artifact(report_type="test_type", seller_id=None, is_deleted=False, file_path=None):
    return ReportArtifactModel(
        report_type=report_type,
        format="csv",
        generated_by="test_user",
        trigger_source="pytest",
        seller_account_id=seller_id,
        is_deleted=is_deleted,
        file_path=file_path
    )

# 1. create_artifact
def test_create_artifact(repo):
    art = create_mock_artifact()
    rid = repo.create_artifact(art)
    assert rid is not None
    assert isinstance(rid, str)

# 2. get_artifact_by_id
def test_get_artifact_by_id(repo):
    art = create_mock_artifact()
    rid = repo.create_artifact(art)
    fetched = repo.get_artifact_by_id(rid)
    assert fetched is not None
    assert fetched.report_id == rid

# 3. get_artifact_by_id not found
def test_get_artifact_not_found(repo):
    assert repo.get_artifact_by_id("non_existent") is None

# 4. list_recent_artifacts (order and limit)
def test_list_recent_artifacts(repo):
    for i in range(5):
        repo.create_artifact(create_mock_artifact())
    recent = repo.list_recent_artifacts(limit=3)
    assert len(recent) == 3

# 5. list_by_report_type
def test_list_by_report_type(repo):
    repo.create_artifact(create_mock_artifact(report_type="A"))
    repo.create_artifact(create_mock_artifact(report_type="A"))
    repo.create_artifact(create_mock_artifact(report_type="B"))
    
    arts_a = repo.list_by_report_type("A")
    assert len(arts_a) == 2
    assert all(a.report_type == "A" for a in arts_a)

# 6. list_by_seller
def test_list_by_seller(repo):
    repo.create_artifact(create_mock_artifact(seller_id="seller1"))
    repo.create_artifact(create_mock_artifact(seller_id="seller2"))
    
    seller1_arts = repo.list_by_seller("seller1")
    assert len(seller1_arts) == 1
    assert seller1_arts[0].seller_account_id == "seller1"

# 7. update_artifact success
def test_update_artifact(repo):
    art = create_mock_artifact(file_path="old_path")
    rid = repo.create_artifact(art)
    
    updated = repo.update_artifact(rid, {"file_path": "new_path"})
    assert updated is True
    
    fetched = repo.get_artifact_by_id(rid)
    assert fetched.file_path == "new_path"

# 8. update_artifact not found
def test_update_artifact_not_found(repo):
    assert repo.update_artifact("non_existent", {"file_path": "new"}) is False

# 9. soft_delete
def test_soft_delete(repo):
    art = create_mock_artifact()
    rid = repo.create_artifact(art)
    
    deleted = repo.soft_delete(rid)
    assert deleted is True
    
    fetched = repo.get_artifact_by_id(rid)
    assert fetched.is_deleted is True

# 10. get_active_artifacts ignores deleted
def test_get_active_artifacts(repo):
    repo.create_artifact(create_mock_artifact(is_deleted=False))
    repo.create_artifact(create_mock_artifact(is_deleted=True))
    
    active = repo.get_active_artifacts()
    assert len(active) == 1
    assert active[0].is_deleted is False

# 11. Test expiry field exists and is nullable
def test_expiry_field(repo):
    art = create_mock_artifact()
    art.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    rid = repo.create_artifact(art)
    fetched = repo.get_artifact_by_id(rid)
    assert fetched.expires_at is not None

# 12. Test blob_ref field
def test_blob_ref_field(repo):
    art = create_mock_artifact()
    art.blob_ref = "s3://bucket/path"
    rid = repo.create_artifact(art)
    fetched = repo.get_artifact_by_id(rid)
    assert fetched.blob_ref == "s3://bucket/path"

# 13. Test created_at and updated_at
def test_timestamps(repo):
    art = create_mock_artifact()
    rid = repo.create_artifact(art)
    fetched = repo.get_artifact_by_id(rid)
    assert fetched.created_at is not None
    assert fetched.updated_at is not None
