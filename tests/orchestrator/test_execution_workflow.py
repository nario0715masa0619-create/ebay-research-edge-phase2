import pytest
import os
from src.orchestrator.execution_workflow import ExecutionWorkflow
from src.listing_execution.cli import get_service

@pytest.fixture
def workflow():
    service = get_service()
    return ExecutionWorkflow(service)

@pytest.fixture
def clean_env():
    token = os.environ.pop("EBAY_AUTH_TOKEN", None)
    app_id = os.environ.pop("EBAY_APP_ID", None)
    cert_id = os.environ.pop("EBAY_CERT_ID", None)
    yield
    if token: os.environ["EBAY_AUTH_TOKEN"] = token
    if app_id: os.environ["EBAY_APP_ID"] = app_id
    if cert_id: os.environ["EBAY_CERT_ID"] = cert_id

def test_orchestrator_dry_run_workflow(workflow):
    payload = {
        "listing_id": "lst_orch_001",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    result = workflow.execute_listing_workflow(payload, dry_run=True)
    assert result["status"] == "success"
    assert result["dry_run"] is True

def test_orchestrator_live_workflow_missing_credentials(workflow, clean_env):
    payload = {
        "listing_id": "lst_orch_002",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    result = workflow.execute_listing_workflow(payload, dry_run=False)
    assert result["status"] == "failed"
    assert "Missing credentials" in result["error_reason"]

def test_orchestrator_live_workflow_with_explicit_credentials(workflow, clean_env):
    payload = {
        "listing_id": "lst_orch_003",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    credentials = {
        "auth_token": "token1",
        "app_id": "app1",
        "cert_id": "cert1"
    }
    result = workflow.execute_listing_workflow(payload, dry_run=False, credentials=credentials)
    assert result["status"] == "success"
    assert result["dry_run"] is False

def test_orchestrator_live_workflow_with_env_credentials(workflow, clean_env):
    os.environ["EBAY_AUTH_TOKEN"] = "token123"
    os.environ["EBAY_APP_ID"] = "app123"
    os.environ["EBAY_CERT_ID"] = "cert123"
    
    payload = {
        "listing_id": "lst_orch_004",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    result = workflow.execute_listing_workflow(payload, dry_run=False)
    assert result["status"] == "success"
    assert result["dry_run"] is False
