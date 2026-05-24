import pytest
import json
from unittest.mock import patch, MagicMock
from src.listing_execution.cli import main as cli_main
from src.listing_execution.web import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_web_check_readiness(client):
    payload = {
        "candidate_data": {"title": "X", "price": 100, "sku": "sku_1", "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    response = client.post('/execution/readiness', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_ready"] is True
    assert data["score"] == 100.0

def test_web_execute_listing_success(client):
    payload = {
        "attempt_id": "att_web_001",
        "listing_id": "lst_web_001",
        "seller": "seller_A",
        "environment": "sandbox",
        "candidate_data": {"title": "X", "price": 100, "sku": "sku_success", "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    response = client.post('/execution/execute', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["attempt_id"] == "att_web_001"

def test_web_execute_listing_rejected(client):
    payload = {
        "attempt_id": "att_web_002",
        "listing_id": "lst_web_002",
        "seller": "seller_A",
        "environment": "sandbox",
        "candidate_data": {}, # Empty data drops readiness < 80
        "seller_data": {},
        "handoff_data": {}
    }
    response = client.post('/execution/execute', json=payload)
    assert response.status_code == 422
    data = response.get_json()
    assert data["status"] == "rejected"
    assert "error_reason" in data

def test_web_get_attempt(client):
    # First create it
    payload = {
        "attempt_id": "att_web_003",
        "listing_id": "lst_web_003",
        "seller": "seller_A",
        "environment": "sandbox",
        "candidate_data": {"title": "X", "price": 100, "sku": "sku_success", "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    client.post('/execution/execute', json=payload)
    
    response = client.get('/execution/att_web_003')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "executed"
    assert data["listing_id"] == "lst_web_003"

def test_web_rollback_execution(client):
    payload = {
        "attempt_id": "att_web_004",
        "listing_id": "lst_web_004",
        "seller": "seller_A",
        "environment": "sandbox",
        "candidate_data": {"title": "X", "price": 100, "sku": "sku_success", "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    client.post('/execution/execute', json=payload)
    
    rollback_res = client.post('/execution/att_web_004/rollback', json={"reason": "test rollback"})
    assert rollback_res.status_code == 200
    assert rollback_res.get_json()["status"] == "rolled_back"

def test_cli_check_readiness(capsys):
    test_args = [
        "check-readiness",
        "--candidate-data", '{"title": "A", "price": 100, "sku": "sku1", "profitability_score": 100}',
        "--seller-data", '{"is_active": true}',
        "--handoff-data", '{"handoff_status": "ready"}'
    ]
    with patch("sys.argv", ["cli.py"] + test_args):
        cli_main()
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_ready"] is True
    assert output["score"] == 100.0

def test_cli_execute_listing(capsys):
    payload = {
        "attempt_id": "att_cli_001",
        "listing_id": "lst_cli_001",
        "seller": "seller_A",
        "environment": "sandbox",
        "candidate_data": {"title": "X", "price": 100, "sku": "sku_success", "profitability_score": 100},
        "seller_data": {"is_active": True},
        "handoff_data": {"handoff_status": "ready"}
    }
    test_args = [
        "execute-listing",
        "--payload", json.dumps(payload)
    ]
    with patch("sys.argv", ["cli.py"] + test_args):
        cli_main()
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "success"
    assert output["attempt_id"] == "att_cli_001"
