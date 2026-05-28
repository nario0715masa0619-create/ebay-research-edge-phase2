import pytest
import os
from flask import Flask
from werkzeug.exceptions import HTTPException
from src.admin_web.routes.policy_routes import policy_bp, management_service
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel
from uuid import uuid4

@pytest.fixture
def app():
    template_dir = os.path.abspath('src/admin_web/templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config['TESTING'] = True
    app.secret_key = 'test_secret'
    app.register_blueprint(policy_bp)
    
    # Custom error handlers for tests
    @app.errorhandler(400)
    def bad_request(e):
        return str(e.description), 400
        
    @app.errorhandler(404)
    def not_found(e):
        return str(e.description), 404
        
    @app.errorhandler(409)
    def conflict(e):
        return str(e.description), 409
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_management_service():
    management_service.policies.clear()
    management_service.events.clear()
    yield

def test_list_policies(client):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.get('/ops/policies/')
    assert res.status_code == 200
    assert b"T1" in res.data or b"pause_handoff" in res.data

def test_list_policies_filter_status(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    p.status = PolicyStatus.ACTIVE
    res = client.get('/ops/policies/?status=active')
    assert res.status_code == 200
    assert b"active" in res.data

def test_list_policies_filter_scope(client):
    management_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.get('/ops/policies/?scope=seller')
    assert res.status_code == 200
    assert b"seller" in res.data

def test_list_policies_pagination(client):
    for i in range(5):
        management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, f"T{i}", "R", "u")
    res = client.get('/ops/policies/?limit=2')
    assert res.status_code == 200

def test_policy_detail(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.get(f'/ops/policies/{p.policy_id}')
    assert res.status_code == 200
    assert str(p.policy_id).encode() in res.data

def test_policy_detail_not_found(client):
    res = client.get(f'/ops/policies/{uuid4()}')
    assert res.status_code == 404

def test_policy_detail_invalid_uuid(client):
    res = client.get('/ops/policies/invalid-uuid')
    assert res.status_code == 400

def test_dashboard(client):
    management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.get('/ops/policies/dashboard')
    assert res.status_code == 200
    assert b"Total Policies: 1" in res.data

def test_candidates(client):
    res = client.get('/ops/policies/candidates')
    assert res.status_code == 200

def test_create_get(client):
    res = client.get('/ops/policies/create')
    assert res.status_code == 200
    assert b"<form" in res.data

def test_create_post(client):
    data = {
        'action': 'pause_handoff',
        'scope': 'global',
        'title': 'Test Policy',
        'reason': 'Test Reason'
    }
    res = client.post('/ops/policies/create', data=data)
    assert res.status_code == 302 # redirect
    assert len(management_service.policies) == 1

def test_approve_redirect(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.post(f'/ops/policies/{p.policy_id}/approve')
    assert res.status_code == 302
    assert p.status == PolicyStatus.APPROVED

def test_approve_strong_requires_review_due(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.BLOCK_LIVE_EXECUTION, "T1", "R1", "u")
    p.level = PolicyLevel.STRONG
    res = client.post(f'/ops/policies/{p.policy_id}/approve')
    assert res.status_code == 400

def test_activate_state_transition(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    p.status = PolicyStatus.APPROVED
    res = client.post(f'/ops/policies/{p.policy_id}/activate')
    assert res.status_code == 302
    assert p.status == PolicyStatus.ACTIVE

def test_release_state_transition(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    p.status = PolicyStatus.ACTIVE
    res = client.post(f'/ops/policies/{p.policy_id}/release')
    assert res.status_code == 302
    assert p.status == PolicyStatus.RELEASED

def test_reject_state_transition(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.post(f'/ops/policies/{p.policy_id}/reject')
    assert res.status_code == 302
    assert p.status == PolicyStatus.REJECTED

def test_cancel_state_transition(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.post(f'/ops/policies/{p.policy_id}/cancel')
    assert res.status_code == 302
    assert p.status == PolicyStatus.CANCELLED

def test_invalid_transition(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    # Trying to release a PROPOSED policy should fail
    res = client.post(f'/ops/policies/{p.policy_id}/release')
    assert res.status_code == 409

def test_digest_markdown(client):
    p = management_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R1", "u")
    res = client.get(f'/ops/policies/{p.policy_id}/digest')
    assert res.status_code == 200
    assert b"Markdown Content" in res.data
    assert p.title.encode() in res.data

def test_create_missing_fields(client):
    data = {
        'action': 'pause_handoff',
        # scope is missing
        'title': 'Test',
        'reason': 'R'
    }
    res = client.post('/ops/policies/create', data=data)
    assert res.status_code == 400
