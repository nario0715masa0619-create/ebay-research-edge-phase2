import pytest
import json
from flask import Flask
from src.admin_web.routes.report_routes import report_bp

@pytest.fixture
def app():
    app = Flask(__name__, template_folder='../../src/admin_web/templates')
    app.register_blueprint(report_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_report_list_get(client):
    res = client.get('/execution/reports')
    assert res.status_code == 200
    assert b'Report List' in res.data
    assert b'Filter' in res.data

def test_summary_preview_default(client):
    res = client.get('/execution/reports/summary?period=daily')
    assert res.status_code == 200
    assert b'Summary Preview' in res.data
    assert b'total_executions' in res.data
    assert b'table' in res.data

def test_summary_preview_json(client):
    res = client.get('/execution/reports/summary?period=daily&format=json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data[0]['metric'] == 'total_executions'

def test_summary_preview_invalid_format(client):
    res = client.get('/execution/reports/summary?period=daily&format=xml')
    assert res.status_code == 400
    assert b'table' in res.data  # fallback

def test_failure_digest_default(client):
    res = client.get('/execution/reports/failures')
    assert res.status_code == 200
    assert b'Failure Digest' in res.data
    assert b'timeout' in res.data

def test_failure_digest_json(client):
    res = client.get('/execution/reports/failures?format=json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data[0]['error'] == 'timeout'

def test_failure_digest_invalid_date(client):
    res = client.get('/execution/reports/failures?from_date=2023-01-02&to_date=2023-01-01')
    assert res.status_code == 400
    assert b'invalid date_range' in res.data

def test_alert_digest_default(client):
    res = client.get('/execution/reports/alerts')
    assert res.status_code == 200
    assert b'Alert Digest' in res.data
    assert b'high_cpu' in res.data

def test_alert_digest_json(client):
    res = client.get('/execution/reports/alerts?format=json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data[0]['alert'] == 'high_cpu'

def test_seller_health_default(client):
    res = client.get('/execution/reports/sellers?seller=test_seller')
    assert res.status_code == 200
    assert b'Seller Health' in res.data
    assert b'healthy' in res.data

def test_seller_health_json(client):
    res = client.get('/execution/reports/sellers?seller=test_seller&format=json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data[0]['status'] == 'healthy'

def test_seller_health_not_found(client):
    res = client.get('/execution/reports/sellers?seller=unknown')
    assert res.status_code == 404

def test_artifact_detail_default(client):
    res = client.get('/execution/reports/artifacts/art-1')
    assert res.status_code == 200
    assert b'Artifact Detail' in res.data

def test_artifact_detail_json(client):
    res = client.get('/execution/reports/artifacts/art-1?format=json')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data[0]['report_id'] == 'art-1'

def test_artifact_detail_not_found(client):
    res = client.get('/execution/reports/artifacts/unknown')
    assert res.status_code == 404

def test_read_only_enforcement_list(client):
    res = client.get('/execution/reports')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_read_only_enforcement_summary(client):
    res = client.get('/execution/reports/summary')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_read_only_enforcement_failures(client):
    res = client.get('/execution/reports/failures')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_read_only_enforcement_alerts(client):
    res = client.get('/execution/reports/alerts')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_read_only_enforcement_sellers(client):
    res = client.get('/execution/reports/sellers?seller=s1')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_read_only_enforcement_artifacts(client):
    res = client.get('/execution/reports/artifacts/art-1')
    assert b'edit' not in res.data.lower()
    assert b'delete' not in res.data.lower()

def test_invalid_format_failures(client):
    res = client.get('/execution/reports/failures?format=invalid')
    assert res.status_code == 400
    assert b'Table' in res.data

def test_invalid_format_alerts(client):
    res = client.get('/execution/reports/alerts?format=xyz')
    assert res.status_code == 400
    assert b'Table' in res.data
