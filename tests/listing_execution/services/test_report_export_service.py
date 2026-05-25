import pytest
import json
import csv
import io
from datetime import datetime, timezone
from src.listing_execution.services.report_export_service import ReportExportService
from src.listing_execution.models.health_report import SellerHealthReport
from src.listing_execution.models.report_artifact import ReportArtifact
from src.listing_execution.models.report_metadata import ReportMetadata
from src.listing_execution.repositories.report_artifact_repository import ReportArtifactRepository

@pytest.fixture
def export_service():
    return ReportExportService()

@pytest.fixture
def artifact_repo():
    return ReportArtifactRepository()

def test_export_summary_to_json(export_service):
    summary = {"total_executed": 100, "succeeded": 90}
    result = export_service.export_summary_to_json(summary)
    data = json.loads(result)
    assert data["total_executed"] == 100
    assert data["succeeded"] == 90

def test_export_summary_to_csv(export_service):
    summary = {"seller": "seller_1", "total_executed": 100, "date_range": ("2026-05-01", "2026-05-31")}
    result = export_service.export_summary_to_csv(summary)
    
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["seller"] == "seller_1"
    assert rows[0]["total_executed"] == "100"
    assert rows[0]["date_range_start"] == "2026-05-01"
    assert rows[0]["date_range_end"] == "2026-05-31"

def test_export_failure_digest_to_csv(export_service):
    digest = {
        "recent_failures": [
            {"event_id": "e1", "attempt_id": "a1", "error_code": "ERR1", "created_at": "2026-05-25T10:00:00Z"}
        ]
    }
    result = export_service.export_failure_digest_to_csv(digest)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["event_id"] == "e1"
    assert rows[0]["error_code"] == "ERR1"

def test_export_alert_digest_to_csv(export_service):
    digest = {
        "recent_alerts": [
            {"event_id": "e1", "event_type": "alert_created", "details": {"alert_level": "WARNING"}}
        ]
    }
    result = export_service.export_alert_digest_to_csv(digest)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["event_id"] == "e1"
    assert rows[0]["alert_level"] == "WARNING"

def test_export_seller_health_to_csv(export_service):
    report = SellerHealthReport(
        seller_id="seller_1",
        date_range=("2026-05-01", "2026-05-31"),
        execution_volume=100,
        failure_rate=0.05,
        guard_rejection_count=2,
        retry_rollback_count=1,
        major_error_patterns=[("ERR1", 5)]
    )
    result = export_service.export_seller_health_to_csv(report)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["seller_id"] == "seller_1"
    assert rows[0]["execution_volume"] == "100"
    assert rows[0]["date_range_start"] == "2026-05-01"

def test_export_execution_audit_to_json(export_service):
    history = [
        {"event_id": "e1", "event_type": "execution_started", "dry_run": True}
    ]
    result = export_service.export_execution_audit_to_json(history)
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["event_id"] == "e1"

# --- Repository Tests ---

def test_create_and_get_artifact(artifact_repo):
    meta = ReportMetadata(
        report_id="", report_type="summary", format="json",
        generated_at=datetime.now(timezone.utc), generated_by="system",
        filter_snapshot={}, row_count=10, applied_filters={"seller_account_id": "seller_1"}
    )
    artifact = ReportArtifact(metadata=meta, artifact_path="/tmp/1")
    
    a_id = artifact_repo.create_artifact(artifact)
    assert a_id is not None
    assert a_id != ""
    
    fetched = artifact_repo.get_artifact_by_id(a_id)
    assert fetched is not None
    assert fetched.metadata.report_type == "summary"

def test_list_recent_artifacts(artifact_repo):
    for i in range(5):
        meta = ReportMetadata(
            report_id=f"id_{i}", report_type="summary", format="json",
            generated_at=datetime.now(timezone.utc), generated_by="system",
            filter_snapshot={}, row_count=10, applied_filters={}
        )
        artifact_repo.create_artifact(ReportArtifact(metadata=meta))
    
    recent = artifact_repo.list_recent_artifacts(limit=3)
    assert len(recent) == 3

def test_list_by_report_type(artifact_repo):
    meta1 = ReportMetadata(
        report_id="1", report_type="summary", format="json",
        generated_at=datetime.now(timezone.utc), generated_by="system",
        filter_snapshot={}, row_count=10, applied_filters={}
    )
    meta2 = ReportMetadata(
        report_id="2", report_type="digest", format="json",
        generated_at=datetime.now(timezone.utc), generated_by="system",
        filter_snapshot={}, row_count=10, applied_filters={}
    )
    artifact_repo.create_artifact(ReportArtifact(metadata=meta1))
    artifact_repo.create_artifact(ReportArtifact(metadata=meta2))
    
    by_type = artifact_repo.list_by_report_type("digest")
    assert len(by_type) == 1
    assert by_type[0].metadata.report_id == "2"

def test_list_by_seller(artifact_repo):
    meta1 = ReportMetadata(
        report_id="1", report_type="summary", format="json",
        generated_at=datetime.now(timezone.utc), generated_by="system",
        filter_snapshot={}, row_count=10, applied_filters={"seller_account_id": "seller_1"}
    )
    meta2 = ReportMetadata(
        report_id="2", report_type="summary", format="json",
        generated_at=datetime.now(timezone.utc), generated_by="system",
        filter_snapshot={}, row_count=10, applied_filters={"seller_account_id": "seller_2"}
    )
    artifact_repo.create_artifact(ReportArtifact(metadata=meta1))
    artifact_repo.create_artifact(ReportArtifact(metadata=meta2))
    
    by_seller = artifact_repo.list_by_seller("seller_1")
    assert len(by_seller) == 1
    assert by_seller[0].metadata.report_id == "1"
