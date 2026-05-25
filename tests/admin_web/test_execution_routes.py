import pytest
from src.admin_web.execution_routes import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_web_execute_dry_run(client):
    payload = {
        "listing_id": "lst_web_001",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"},
        "dry_run": True
    }
    response = client.post('/execution/execute/live', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["dry_run"] is True

def test_web_execute_live_no_credentials(client):
    payload = {
        "listing_id": "lst_web_002",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"},
        "dry_run": False
    }
    response = client.post('/execution/execute/live', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "failed"
    assert "Missing credentials" in data["error_reason"]

def test_web_execute_live_with_header_credentials(client):
    payload = {
        "listing_id": "lst_web_003",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"},
        "dry_run": False
    }
    headers = {
        "Authorization": "Bearer webtoken123"
    }
    response = client.post('/execution/execute/live', json=payload, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["dry_run"] is False

def test_web_execute_live_with_body_credentials(client):
    payload = {
        "listing_id": "lst_web_004",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"},
        "dry_run": False,
        "credentials": {
            "auth_token": "body_token",
            "app_id": "app_id",
            "cert_id": "cert_id"
        }
    }
    response = client.post('/execution/execute/live', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["dry_run"] is False

def test_web_get_full_attempt(client):
    payload = {
        "attempt_id": "att_full_001",
        "listing_id": "lst_full_001",
        "seller": "seller_A",
        "sku": "sku_success",
        "candidate_data": {"title": "X", "price": 100, "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"},
        "dry_run": False,
        "credentials": {
            "auth_token": "token",
            "app_id": "app",
            "cert_id": "cert"
        }
    }
    response_post = client.post('/execution/execute/live', json=payload)
    assert response_post.status_code == 200
    
    response = client.get('/execution/att_full_001/full')
    assert response.status_code == 200
    data = response.get_json()
    
    assert "execution_result" in data
    assert data["execution_result"]["attempt_id"] == "att_full_001"
    assert data["execution_result"]["status"] == "executed"
    assert data["listing_state"] == "active"
    assert data["alert_level"] == "INFO"
    assert "retry_info" in data
