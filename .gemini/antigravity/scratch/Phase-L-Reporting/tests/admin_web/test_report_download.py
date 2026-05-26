import pytest
from src.admin_web.routes.report_routes import report_bp
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(report_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# 14. web download route success
def test_web_download_success(client):
    res = client.get('/execution/reports/artifacts/test-id/download')
    assert res.status_code == 200
    assert 'attachment' in res.headers.get('Content-Disposition', '')
    assert 'test-id.txt' in res.headers.get('Content-Disposition', '')

# 15. web download expired
def test_web_download_expired(client):
    res = client.get('/execution/reports/artifacts/test-id/download?expired=true')
    assert res.status_code == 410

# 16. web download deleted
def test_web_download_deleted(client):
    res = client.get('/execution/reports/artifacts/test-id/download?deleted=true')
    assert res.status_code == 404

# 19. web download format validation (ValueError test mock)
def test_web_download_value_error(client, monkeypatch):
    from src.services.report_services import ReportExportService
    def mock_show(*args, **kwargs):
        raise ValueError("invalid input")
    monkeypatch.setattr(ReportExportService, "show_report", mock_show)
    res = client.get('/execution/reports/artifacts/test-id/download')
    assert res.status_code == 400

# 20. repo list recent empty
def test_repo_empty(client):
    pass
