import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from src.learning.services.root_cause_analysis_service import RootCauseAnalysisService

@pytest.fixture
def service():
    return RootCauseAnalysisService()

def test_create_rca(service):
    lid = uuid4()
    rca = service.create_rca(
        learning_record_id=lid,
        problem="P1",
        symptoms="S1",
        cause="C1",
        factors="F1",
        mitigation="M1",
        resolution="R1",
        prevention="PR1",
        created_by="u1",
        evidence={"k": "v"}
    )
    assert rca.problem_statement == "P1"
    assert rca.evidence_snapshot == {"k": "v"}
    assert rca.learning_record_id == lid

def test_get_rca_by_id_found(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR", "u")
    found = service.get_rca_by_id(rca.rca_id)
    assert found is not None
    assert found.rca_id == rca.rca_id

def test_get_rca_by_id_not_found(service):
    assert service.get_rca_by_id(uuid4()) is None

def test_get_rcas_by_learning_record(service):
    lid1 = uuid4()
    lid2 = uuid4()
    rca1 = service.create_rca(lid1, "P", "S", "C", "F", "M", "R", "PR", "u")
    rca2 = service.create_rca(lid1, "P2", "S", "C", "F", "M", "R", "PR", "u")
    rca3 = service.create_rca(lid2, "P3", "S", "C", "F", "M", "R", "PR", "u")
    
    rcas = service.get_rcas_by_learning_record(lid1)
    assert len(rcas) == 2
    assert rca1 in rcas
    assert rca2 in rcas
    assert rca3 not in rcas

def test_update_rca(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR", "u")
    
    updated = service.update_rca(rca.rca_id, problem="NewP", cause="NewC", resolution="NewR")
    assert updated.problem_statement == "NewP"
    assert updated.primary_cause == "NewC"
    assert updated.resolution_summary == "NewR"

def test_add_detection_gap_analysis(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR", "u")
    
    updated = service.add_detection_gap_analysis(rca.rca_id, "Gap found")
    assert updated.detection_gap == "Gap found"

def test_extract_prevention_proposal(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR123", "u")
    
    proposal = service.extract_prevention_proposal(rca.rca_id)
    assert "Prevention Proposal for RCA" in proposal
    assert "PR123" in proposal

def test_evidence_snapshot_preserved(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR", "u", evidence={"e": "v"})
    
    updated = service.update_rca(rca.rca_id, problem="NewP")
    assert updated.evidence_snapshot == {"e": "v"}

def test_rca_created_at_immutable(service):
    lid = uuid4()
    rca = service.create_rca(lid, "P", "S", "C", "F", "M", "R", "PR", "u")
    orig_created = rca.created_at
    
    updated = service.update_rca(rca.rca_id, problem="NewP")
    assert updated.created_at == orig_created

def test_multiple_rcas_per_learning_record(service):
    lid = uuid4()
    service.create_rca(lid, "P1", "S", "C", "F", "M", "R", "PR", "u")
    service.create_rca(lid, "P2", "S", "C", "F", "M", "R", "PR", "u")
    service.create_rca(lid, "P3", "S", "C", "F", "M", "R", "PR", "u")
    
    assert len(service.get_rcas_by_learning_record(lid)) == 3
