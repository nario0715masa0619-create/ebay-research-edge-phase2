import pytest
import os
from fastapi.testclient import TestClient
from src.admin_web.app import app
from src.admin_web.action_guards import WebActionGuard

client = TestClient(app)

def test_read_only_mode_blocks_post_actions(monkeypatch):
    # Set read-only mode active
    monkeypatch.setenv("ADMIN_WEB_READ_ONLY_MODE", "true")
    
    # Verify triggering a POST action fails with 403 Forbidden
    data = {
        "job_name": "research",
        "seller_account_id": "TEST-SELLER",
        "environment_type": "sandbox"
    }
    response = client.post("/admin/jobs/run", data=data)
    assert response.status_code == 403
    assert "READ-ONLY mode" in response.json()["detail"]

def test_environment_mismatch_blocks_actions():
    # Attempting to execute production action under sandbox active context query
    data = {
        "job_name": "research",
        "seller_account_id": "TEST-SELLER",
        "environment_type": "production" # mismatched env target
    }
    response = client.post("/admin/jobs/run?seller_account_id=TEST-SELLER&environment_type=sandbox", data=data)
    assert response.status_code == 400
    assert "Safety Mismatch" in response.json()["detail"]

def test_production_disallowed_safeguard(monkeypatch):
    # Ensure SELLER_ENV_ALLOW_PRODUCTION_PUBLISH is false (default)
    monkeypatch.setenv("SELLER_ENV_ALLOW_PRODUCTION_PUBLISH", "false")
    monkeypatch.setenv("ADMIN_WEB_READ_ONLY_MODE", "false")
    monkeypatch.setenv("ADMIN_WEB_ENABLE_MUTATIONS", "true")
    
    # Activating production context and triggering a publish action
    data = {
        "job_name": "research",
        "seller_account_id": "TEST-SELLER",
        "environment_type": "production"
    }
    # Direct access under production context
    response = client.post("/admin/jobs/run?seller_account_id=TEST-SELLER&environment_type=production", data=data)
    assert response.status_code == 403
    assert "Production mutation is disabled" in response.json()["detail"]
