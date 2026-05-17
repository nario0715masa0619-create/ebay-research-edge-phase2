import pytest
from fastapi.testclient import TestClient
from src.admin_web.app import app

client = TestClient(app)

def test_root_redirection():
    # Verify root redirects to admin
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/admin"

def test_dashboard_route():
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Active Context Connection" in response.text

def test_sellers_route():
    response = client.get("/admin/sellers")
    assert response.status_code == 200
    assert "Sellers Configuration" in response.text
    assert "Seller Label" in response.text

def test_jobs_route():
    response = client.get("/admin/jobs")
    assert response.status_code == 200
    assert "Orchestrator Pipelines" in response.text
    assert "Execution Run History" in response.text

def test_candidates_route():
    response = client.get("/admin/candidates")
    assert response.status_code == 200
    assert "Product Candidates" in response.text
    assert "Filter Candidates" in response.text

def test_listings_route():
    response = client.get("/admin/listings")
    assert response.status_code == 200
    assert "Active Listings" in response.text
    assert "Filter Listings" in response.text

def test_review_route():
    response = client.get("/admin/review")
    assert response.status_code == 200
    assert "Review Queue" in response.text
    assert "Interventions" in response.text

def test_notifications_route():
    response = client.get("/admin/notifications")
    assert response.status_code == 200
    assert "Notification History" in response.text
    assert "Channel Test" in response.text

def test_doctor_route():
    response = client.get("/admin/doctor")
    assert response.status_code == 200
    assert "Doctor" in response.text
    assert "System Diagnostic Checks" in response.text
