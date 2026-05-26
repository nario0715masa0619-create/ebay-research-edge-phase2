import pytest
from uuid import uuid4
from datetime import datetime
from src.learning.repositories.root_cause_analysis_repository_db import RootCauseAnalysisRepository
from src.learning.models.root_cause_analysis import RootCauseAnalysis

@pytest.fixture
def repo():
    return RootCauseAnalysisRepository()

def create_dummy_rca(lid: uuid4 = None) -> RootCauseAnalysis:
    return RootCauseAnalysis(
        rca_id=uuid4(),
        learning_record_id=lid or uuid4(),
        problem_statement="P",
        observed_symptoms="S",
        primary_cause="C",
        contributing_factors="F",
        detection_gap="D",
        mitigation_taken="M",
        resolution_summary="R",
        prevention_proposal="P",
        evidence_snapshot={},
        created_by="u",
        created_at=datetime.utcnow()
    )

def test_create_rca(repo):
    r = create_dummy_rca()
    res = repo.create_rca(r)
    assert res.rca_id == r.rca_id
    assert repo.get_rca_by_id(r.rca_id) is not None

def test_get_rca_by_id_found(repo):
    r = create_dummy_rca()
    repo.create_rca(r)
    assert repo.get_rca_by_id(r.rca_id) == r

def test_get_rcas_by_learning_record(repo):
    lid = uuid4()
    r1 = create_dummy_rca(lid)
    r2 = create_dummy_rca(lid)
    repo.create_rca(r1)
    repo.create_rca(r2)
    res = repo.get_rcas_by_learning_record(lid)
    assert len(res) == 2

def test_list_all_rcas(repo):
    repo.create_rca(create_dummy_rca())
    repo.create_rca(create_dummy_rca())
    res, total = repo.list_all_rcas()
    assert total == 2
    assert len(res) == 2

def test_count_by_learning_record(repo):
    lid = uuid4()
    repo.create_rca(create_dummy_rca(lid))
    repo.create_rca(create_dummy_rca(lid))
    counts = repo.count_rcas_by_learning_record()
    assert counts[lid] == 2
