import pytest
import json
from uuid import uuid4
from datetime import datetime

from src.admin_cli.learning_commands import (
    candidate_scan, list_records, show_record, create_from_incident, add_rca,
    add_recommendation, close_record, learning_digest, recurring_issues,
    false_signals, list_recommendations, approve_recommendation, reject_recommendation,
    learning_dashboard, learning_record_service, root_cause_analysis_service,
    learning_recommendation_service, learning_candidate_service
)
from src.learning.models.learning_record import RootCauseCategory, ImpactScope, LearningRecordStatus
from src.learning.models.learning_recommendation import RecommendationType, RecommendationStatus

class DummyArgs:
    def __init__(self, **kwargs):
        self.format = kwargs.get("format", "table")
        self.output_file = kwargs.get("output_file")
        self.dry_run = kwargs.get("dry_run", False)
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture(autouse=True)
def reset_services():
    learning_record_service.records.clear()
    root_cause_analysis_service.rcas.clear()
    learning_recommendation_service.recommendations.clear()
    learning_candidate_service.candidates.clear()
    yield

def test_candidate_scan(capsys):
    learning_candidate_service.detect_false_positive_cluster("auth_error")
    args = DummyArgs()
    candidate_scan(args)
    captured = capsys.readouterr()
    assert "ID" in captured.out
    assert "false_positive_detected" in captured.out

def test_list_records_all(capsys):
    learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    args = DummyArgs()
    list_records(args)
    captured = capsys.readouterr()
    assert "LEARNING_ID" in captured.out
    assert "detection_false_positive" in captured.out

def test_list_records_filter_by_status(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.DETECTION_FALSE_POSITIVE, ImpactScope.GLOBAL, "u1")
    learning_record_service.close_learning_record(r1.learning_record_id)
    args = DummyArgs(status="closed")
    list_records(args)
    captured = capsys.readouterr()
    assert "closed" in captured.out

def test_list_records_filter_by_category(capsys):
    learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    args = DummyArgs(category="policy_misconfiguration")
    list_records(args)
    captured = capsys.readouterr()
    assert "policy_misconfiguration" in captured.out

def test_list_records_filter_by_seller(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    r1.seller_account_id = "s1"
    args = DummyArgs(seller="s1")
    list_records(args)
    captured = capsys.readouterr()
    assert "s1" in captured.out

def test_list_records_false_positive_only(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    r1.is_false_positive = True
    args = DummyArgs(false_positive_only=True)
    list_records(args)
    captured = capsys.readouterr()
    assert str(r1.learning_record_id) in captured.out

def test_show_detail(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    root_cause_analysis_service.create_rca(r1.learning_record_id, "P", "S", "C", "F", "M", "R", "PR", "u1")
    args = DummyArgs(learning_id=str(r1.learning_record_id))
    show_record(args)
    captured = capsys.readouterr()
    assert str(r1.learning_record_id) in captured.out
    assert "RCAs (1)" in captured.out

def test_show_not_found():
    args = DummyArgs(learning_id=str(uuid4()))
    with pytest.raises(SystemExit):
        show_record(args)

def test_create_from_incident(capsys):
    args = DummyArgs(incident_id=str(uuid4()), category="policy_misconfiguration", title="T1")
    create_from_incident(args)
    captured = capsys.readouterr()
    assert "Created Learning Record" in captured.out

def test_add_rca(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    args = DummyArgs(learning_id=str(r1.learning_record_id), problem="P1", cause="C1", resolution="R1")
    add_rca(args)
    captured = capsys.readouterr()
    assert "Created RCA" in captured.out

def test_add_recommendation(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    args = DummyArgs(learning_id=str(r1.learning_record_id), type="adjust_incident_threshold", target_phase="N", proposal="P", priority=50)
    add_recommendation(args)
    captured = capsys.readouterr()
    assert "Created Recommendation" in captured.out

def test_close_record(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    args = DummyArgs(learning_id=str(r1.learning_record_id))
    close_record(args)
    captured = capsys.readouterr()
    assert "Closed Learning Record" in captured.out

def test_digest_markdown(capsys):
    args = DummyArgs()
    learning_digest(args)
    captured = capsys.readouterr()
    assert "# Learning Digest" in captured.out

def test_recurring_issues(capsys):
    args = DummyArgs()
    recurring_issues(args)
    captured = capsys.readouterr()
    assert "CLUSTER_ID" in captured.out

def test_false_signals(capsys):
    args = DummyArgs()
    false_signals(args)
    captured = capsys.readouterr()
    assert "ID" in captured.out
    assert "fp-1" in captured.out

def test_recommendations_list(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    learning_recommendation_service.create_recommendation(r1.learning_record_id, RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    args = DummyArgs()
    list_recommendations(args)
    captured = capsys.readouterr()
    assert "REC_ID" in captured.out
    assert "adjust_incident_threshold" in captured.out

def test_approve_recommendation(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    rec = learning_recommendation_service.create_recommendation(r1.learning_record_id, RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    args = DummyArgs(recommendation_id=str(rec.recommendation_id))
    approve_recommendation(args)
    captured = capsys.readouterr()
    assert "Approved Recommendation" in captured.out

def test_reject_recommendation(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    rec = learning_recommendation_service.create_recommendation(r1.learning_record_id, RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u1")
    args = DummyArgs(recommendation_id=str(rec.recommendation_id), reason="Bad")
    reject_recommendation(args)
    captured = capsys.readouterr()
    assert "Rejected Recommendation" in captured.out

def test_dashboard(capsys):
    args = DummyArgs()
    learning_dashboard(args)
    captured = capsys.readouterr()
    assert "LEARNING DASHBOARD" in captured.out
    assert "Total Records" in captured.out

def test_format_json(capsys):
    r1 = learning_record_service.create_learning_record("T1", "S1", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u1")
    args = DummyArgs(format="json")
    list_records(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["CATEGORY"] == "policy_misconfiguration"
