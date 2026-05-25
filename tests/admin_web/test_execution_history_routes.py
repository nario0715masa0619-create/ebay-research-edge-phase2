import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.admin_web.app import app
from src.listing_execution.models.history_query import HistoryEventView
from src.listing_execution.models.dashboard_summary import DashboardSummary
from datetime import datetime

client = TestClient(app)

# Bypass auth for testing
app.dependency_overrides = {}

@pytest.fixture
def mock_auth():
    # Because app.include_router adds the Depends(authenticate_user), 
    # we might need to override the authenticate_user dependency.
    from src.admin_web.app import authenticate_user
    app.dependency_overrides[authenticate_user] = lambda: "admin"
    yield
    app.dependency_overrides.clear()

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_200(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {"items": [], "total": 0}
    response = client.get("/execution/history")
    assert response.status_code == 200
    assert b"Execution History" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_render(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {
        "items": [
            HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="started", dry_run=True, from_state="", to_state="", error_code="ERR1", error_message="", details={}, created_at=datetime.now(), created_by="")
        ],
        "total": 1
    }
    response = client.get("/execution/history")
    assert b"a1" in response.content
    assert b"l1" in response.content
    assert b"started" in response.content
    assert b"ERR1" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_attempt_id_filter(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {"items": [], "total": 0}
    response = client.get("/execution/history?attempt_id=test_att")
    assert response.status_code == 200
    args, kwargs = instance.apply_filters.call_args
    assert args[0].attempt_id == "test_att"

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_listing_id_filter(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {"items": [], "total": 0}
    response = client.get("/execution/history?listing_id=test_list")
    assert response.status_code == 200
    args, kwargs = instance.apply_filters.call_args
    assert args[0].listing_id == "test_list"

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_event_type_filter(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {"items": [], "total": 0}
    response = client.get("/execution/history?event_type=execution_failed")
    assert response.status_code == 200
    args, kwargs = instance.apply_filters.call_args
    assert args[0].event_type == "execution_failed"

@patch('src.admin_web.routes.execution_history.ExecutionHistoryQueryService')
def test_history_list_dry_run_filter(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {"items": [], "total": 0}
    response = client.get("/execution/history?dry_run=True")
    assert response.status_code == 200
    args, kwargs = instance.apply_filters.call_args
    assert args[0].dry_run is True

@patch('src.admin_web.routes.execution_history.ExecutionAuditTimelineService')
def test_attempt_detail_200(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.build_attempt_timeline.return_value = []
    instance.extract_state_transitions.return_value = []
    instance.filter_critical_events.return_value = []
    
    response = client.get("/execution/history/attempt/a1")
    assert response.status_code == 200
    assert b"Attempt: a1" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionAuditTimelineService')
def test_attempt_detail_timeline_render(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.build_attempt_timeline.return_value = [
        HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="execution_failed", dry_run=True, from_state="", to_state="", error_code="ERR_TL", error_message="Timeline error msg", details={}, created_at=datetime.now(), created_by="")
    ]
    instance.extract_state_transitions.return_value = []
    instance.filter_critical_events.return_value = []
    
    response = client.get("/execution/history/attempt/a1")
    assert b"execution_failed" in response.content
    assert b"ERR_TL" in response.content
    assert b"Timeline error msg" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionAuditTimelineService')
def test_listing_detail_200(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.build_listing_timeline.return_value = []
    
    response = client.get("/execution/history/listing/l1")
    assert response.status_code == 200
    assert b"Listing History: l1" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionAuditTimelineService')
def test_listing_detail_multiple_attempts(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.build_listing_timeline.return_value = [
        HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="started", dry_run=True, from_state="", to_state="", error_code="", error_message="", details={}, created_at=datetime.now(), created_by=""),
        HistoryEventView(event_id="e2", attempt_id="a2", listing_id="l1", event_type="execution_failed", dry_run=True, from_state="", to_state="", error_code="ERR2", error_message="", details={}, created_at=datetime.now(), created_by="")
    ]
    
    response = client.get("/execution/history/listing/l1")
    assert response.status_code == 200
    assert b"a1" in response.content
    assert b"a2" in response.content
    assert b"execution_failed" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionDashboardService')
def test_dashboard_200(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=0, succeeded=0, failed=0, rolled_back=0, alert_count=0,
        success_rate=0.0, failure_rate=0.0, alert_level_distribution={},
        top_error_codes=[], top_failure_boundaries=[], dry_run_count=0, live_count=0,
        seller_failure_rates={}, environment_failure_rates={}, guard_rejection_count={}
    )
    instance.get_recent_failures.return_value = []
    
    response = client.get("/execution/dashboard")
    assert response.status_code == 200
    assert b"Execution Dashboard" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionDashboardService')
def test_dashboard_summary_render(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=100, succeeded=80, failed=20, rolled_back=5, alert_count=3,
        success_rate=0.8, failure_rate=0.2, alert_level_distribution={},
        top_error_codes=[("ERR_DB", 10)], top_failure_boundaries=[], dry_run_count=50, live_count=50,
        seller_failure_rates={"seller1": 0.5}, environment_failure_rates={}, guard_rejection_count={"Guard A": 2}
    )
    instance.get_recent_failures.return_value = []
    
    response = client.get("/execution/dashboard")
    assert b"100" in response.content
    assert b"80.0%" in response.content
    assert b"ERR_DB" in response.content
    assert b"Guard A" in response.content
    assert b"seller1" in response.content

@patch('src.admin_web.routes.execution_history.ExecutionDashboardService')
def test_dashboard_recent_failures(mock_service, mock_auth):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=0, succeeded=0, failed=0, rolled_back=0, alert_count=0,
        success_rate=0.0, failure_rate=0.0, alert_level_distribution={},
        top_error_codes=[], top_failure_boundaries=[], dry_run_count=0, live_count=0,
        seller_failure_rates={}, environment_failure_rates={}, guard_rejection_count={}
    )
    instance.get_recent_failures.return_value = [("fail_att_1", None)]
    
    response = client.get("/execution/dashboard")
    assert b"fail_att_1" in response.content

def test_readonly_methods(mock_auth):
    response = client.post("/execution/history")
    assert response.status_code == 405
    
    response = client.delete("/execution/history/attempt/a1")
    assert response.status_code == 405

def test_existing_routes_not_broken():
    # just an example sanity check on root
    response = client.get("/")
    assert response.status_code == 200 or response.status_code == 307
