import pytest
from flask import Flask
from uuid import uuid4
from datetime import datetime

from src.admin_web.routes.learning_routes import (
    learning_bp, learning_record_service, root_cause_analysis_service,
    learning_recommendation_service, learning_candidate_service
)
from src.learning.models.learning_record import RootCauseCategory, ImpactScope, LearningRecordStatus
from src.learning.models.learning_recommendation import RecommendationType

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test_secret"
    # Dummy layout.html is simulated by overriding jinja loader or just allowing exceptions if not present
    # Flask will error if template not found, so we'll mock render_template if needed, or provide dummy templates.
    # Actually, since we created templates in src/admin_web/templates, we can just point the app to it.
    import os
    app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/admin_web/templates'))
    app.register_blueprint(learning_bp)
    
    # Create dummy layout.html so templates can render
    layout_path = os.path.join(app.template_folder, 'layout.html')
    if not os.path.exists(layout_path):
        with open(layout_path, 'w') as f:
            f.write("{% block content %}{% endblock %}")
            
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_services():
    learning_record_service.records.clear()
    root_cause_analysis_service.rcas.clear()
    learning_recommendation_service.recommendations.clear()
    learning_candidate_service.candidates.clear()
    yield

def test_list_records_rendered(client):
    res = client.get('/ops/learning/')
    assert res.status_code == 200
    assert b"Learning Records" in res.data

def test_list_records_filter_by_status(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.ENVIRONMENT_INSTABILITY, ImpactScope.GLOBAL, "u")
    learning_record_service.close_learning_record(r1.learning_record_id)
    res = client.get('/ops/learning/?status=closed')
    assert res.status_code == 200
    assert b"closed" in res.data

def test_list_records_filter_by_category(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    res = client.get('/ops/learning/?category=policy_misconfiguration')
    assert res.status_code == 200
    assert str(r1.learning_record_id).encode() in res.data

def test_list_records_filter_by_seller(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    r1.seller_account_id = "sell1"
    res = client.get('/ops/learning/?seller=sell1')
    assert res.status_code == 200
    assert b"sell1" in res.data

def test_list_records_pagination(client):
    res = client.get('/ops/learning/?limit=10')
    assert res.status_code == 200

def test_detail_view_rendered(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    res = client.get(f'/ops/learning/{r1.learning_record_id}')
    assert res.status_code == 200
    assert b"Learning Record Detail" in res.data

def test_detail_not_found(client):
    res = client.get(f'/ops/learning/{uuid4()}')
    assert res.status_code == 404

def test_detail_invalid_uuid(client):
    res = client.get('/ops/learning/invalid-uuid')
    assert res.status_code == 400

def test_dashboard_summary(client):
    res = client.get('/ops/learning/dashboard')
    assert res.status_code == 200
    assert b"Learning Dashboard" in res.data

def test_recommendations_list(client):
    res = client.get('/ops/learning/recommendations')
    assert res.status_code == 200
    assert b"Recommendations" in res.data

def test_recurring_cluster_list(client):
    res = client.get('/ops/learning/recurring')
    assert res.status_code == 200
    assert b"Recurring Issue Clusters" in res.data

def test_candidates_list(client):
    learning_candidate_service.detect_false_positive_cluster("auth_error")
    res = client.get('/ops/learning/candidates')
    assert res.status_code == 200
    assert b"Learning Candidates" in res.data
    assert b"false_positive_detected" in res.data

def test_add_rca(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    res = client.post(f'/ops/learning/{r1.learning_record_id}/add-rca', data={
        "problem": "P", "cause": "C", "resolution": "R", "prevention": "Pr"
    })
    assert res.status_code == 302
    assert len(root_cause_analysis_service.rcas) == 1

def test_add_recommendation(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    res = client.post(f'/ops/learning/{r1.learning_record_id}/add-recommendation', data={
        "type": "adjust_incident_threshold", "target_phase": "N", "proposal_summary": "P", "priority": "50"
    })
    assert res.status_code == 302
    assert len(learning_recommendation_service.recommendations) == 1

def test_close_record(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    res = client.post(f'/ops/learning/{r1.learning_record_id}/close')
    assert res.status_code == 302
    assert learning_record_service.records[r1.learning_record_id].status == LearningRecordStatus.CLOSED

def test_approve_recommendation(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    rec = learning_recommendation_service.create_recommendation(
        r1.learning_record_id, RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u"
    )
    res = client.post(f'/ops/learning/recommendation/{rec.recommendation_id}/approve')
    assert res.status_code == 302

def test_reject_recommendation(client):
    r1 = learning_record_service.create_learning_record("T", "S", RootCauseCategory.POLICY_MISCONFIGURATION, ImpactScope.GLOBAL, "u")
    rec = learning_recommendation_service.create_recommendation(
        r1.learning_record_id, RecommendationType.ADJUST_INCIDENT_THRESHOLD, "N", "s", "S", "D", 50, datetime.utcnow(), "u"
    )
    res = client.post(f'/ops/learning/recommendation/{rec.recommendation_id}/reject', data={"reason": "bad"})
    assert res.status_code == 302

def test_add_rca_invalid_uuid(client):
    res = client.post('/ops/learning/invalid/add-rca')
    assert res.status_code == 400

def test_add_rca_not_found(client):
    res = client.post(f'/ops/learning/{uuid4()}/add-rca')
    assert res.status_code == 404

def test_approve_recommendation_not_found(client):
    res = client.post(f'/ops/learning/recommendation/{uuid4()}/approve')
    assert res.status_code == 404
