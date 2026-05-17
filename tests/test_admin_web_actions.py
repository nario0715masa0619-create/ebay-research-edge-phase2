import pytest
from fastapi.testclient import TestClient
from src.admin_web.app import app

client = TestClient(app)

def test_activate_seller_context_action():
    # Test switching active seller/environment context
    data = {
        "seller_account_id": "TEST-SELLER",
        "environment_type": "sandbox"
    }
    response = client.post("/admin/sellers/activate", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "seller_account_id=TEST-SELLER" in response.headers["location"]
    assert "environment_type=sandbox" in response.headers["location"]

def test_trigger_test_notification_action():
    data = {
        "event_type": "test_alert",
        "severity": "info",
        "seller_account_id": "TEST-SELLER",
        "environment_type": "sandbox"
    }
    response = client.post("/admin/notifications/test", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "notifications" in response.headers["location"]

def test_trigger_job_run_action():
    data = {
        "job_name": "monitoring",
        "seller_account_id": "TEST-SELLER",
        "environment_type": "sandbox"
    }
    response = client.post("/admin/jobs/run", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "jobs" in response.headers["location"]

def test_trigger_scheduler_once_action():
    data = {
        "seller_account_id": "TEST-SELLER",
        "environment_type": "sandbox"
    }
    response = client.post("/admin/scheduler/run-once", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "dashboard" in response.headers["location"]
