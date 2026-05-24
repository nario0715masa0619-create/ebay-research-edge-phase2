import pytest
from datetime import datetime, timezone
from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.executors.mock_executor import MockExecutor

@pytest.fixture
def base_payload():
    return ExecutionPayload(
        listing_id="list_001",
        seller="seller_a",
        sku="SKU-OK",
        bundle_state="standalone",
        market_eval={},
        profitability_score=100.0,
        environment="sandbox",
        dry_run=False,
        attempt_id="att_001"
    )

@pytest.fixture
def mock_executor():
    rules = {
        "SKU-OK": "success",
        "SKU-TIMEOUT": "timeout",
        "SKU-LIMIT": "seller_limit",
        "SKU-CONFLICT": "state_conflict",
        "SKU-ERROR": "error"
    }
    return MockExecutor(
        allowed_environments=["sandbox", "production"],
        allowed_sellers=["seller_a", "seller_b"],
        fixture_rules=rules
    )

# --- 1. Guard Checks (Environment / Seller) ---

def test_guard_environment_invalid(mock_executor, base_payload):
    base_payload.environment = "invalid_env"
    res = mock_executor.execute(base_payload)
    assert res.status == "error"
    assert "Environment 'invalid_env' is not supported" in res.error_reason

def test_guard_seller_invalid(mock_executor, base_payload):
    base_payload.seller = "unauthorized_seller"
    res = mock_executor.execute(base_payload)
    assert res.status == "error"
    assert "Seller 'unauthorized_seller' is not authorized" in res.error_reason

def test_guard_both_invalid(mock_executor, base_payload):
    base_payload.environment = "invalid_env"
    base_payload.seller = "unauthorized_seller"
    res = mock_executor.execute(base_payload)
    assert res.status == "error"
    assert "Environment 'invalid_env'" in res.error_reason
    assert "Seller 'unauthorized_seller'" in res.error_reason

def test_guard_validation_method_only(mock_executor, base_payload):
    base_payload.seller = "unauthorized_seller"
    val = mock_executor.validate(base_payload)
    assert val.is_valid is False
    assert len(val.error_messages) == 1

# --- 2. Dry Run & Idempotency ---

def test_dry_run_no_state_change(mock_executor, base_payload):
    base_payload.sku = "SKU-ERROR" # Would normally fail
    base_payload.dry_run = True
    res = mock_executor.execute(base_payload)
    
    # Even though SKU points to error, dry_run bypasses actual execution
    assert res.status == "success"
    assert "Simulated" in res.error_reason
    assert len(mock_executor.execution_attempt_records) == 1
    assert mock_executor.execution_attempt_records[0]["is_dry_run"] is True

def test_dry_run_still_checked_for_guards(mock_executor, base_payload):
    base_payload.seller = "bad_seller"
    base_payload.dry_run = True
    res = mock_executor.execute(base_payload)
    # Guards execute before dry_run logic
    assert res.status == "error"

def test_idempotent_cached_result(mock_executor, base_payload):
    # First attempt
    res1 = mock_executor.execute(base_payload)
    assert res1.status == "success"
    assert len(mock_executor.execution_attempt_records) == 1
    
    # Change sku but keep same attempt_id
    base_payload.sku = "SKU-ERROR"
    res2 = mock_executor.execute(base_payload)
    
    # Should return cached success result
    assert res2.status == "success"
    assert res1 is res2
    # Records should not increment
    assert len(mock_executor.execution_attempt_records) == 1

def test_idempotent_different_attempt_id(mock_executor, base_payload):
    res1 = mock_executor.execute(base_payload)
    
    base_payload.attempt_id = "att_002"
    base_payload.sku = "SKU-ERROR"
    res2 = mock_executor.execute(base_payload)
    
    assert res1.status == "success"
    assert res2.status == "error"
    assert len(mock_executor.execution_attempt_records) == 2

# --- 3. Fixture Patterns (Integration) ---

def test_fixture_success(mock_executor, base_payload):
    base_payload.sku = "SKU-OK"
    res = mock_executor.execute(base_payload)
    assert res.status == "success"
    assert res.error_reason is None

def test_fixture_timeout(mock_executor, base_payload):
    base_payload.sku = "SKU-TIMEOUT"
    res = mock_executor.execute(base_payload)
    assert res.status == "timeout"
    assert "Timeout" in res.error_reason

def test_fixture_seller_limit(mock_executor, base_payload):
    base_payload.sku = "SKU-LIMIT"
    res = mock_executor.execute(base_payload)
    assert res.status == "seller_limit"
    assert "exceeded limits" in res.error_reason

def test_fixture_state_conflict(mock_executor, base_payload):
    base_payload.sku = "SKU-CONFLICT"
    res = mock_executor.execute(base_payload)
    assert res.status == "state_conflict"
    assert "Duplicate listing" in res.error_reason

def test_fixture_error(mock_executor, base_payload):
    base_payload.sku = "SKU-ERROR"
    res = mock_executor.execute(base_payload)
    assert res.status == "error"
    assert "Unknown internal" in res.error_reason

def test_fixture_default_success(mock_executor, base_payload):
    base_payload.sku = "UNKNOWN-SKU"
    res = mock_executor.execute(base_payload)
    # If not in rules, defaults to success
    assert res.status == "success"

# --- 4. Extra Tests for robustness ---

def test_execution_attempt_records_content(mock_executor, base_payload):
    mock_executor.execute(base_payload)
    record = mock_executor.execution_attempt_records[0]
    assert record["attempt_id"] == "att_001"
    assert record["listing_id"] == "list_001"
    assert record["status"] == "success"
    assert record["error_reason"] is None
    assert record["is_dry_run"] is False

def test_supports_environment_production(mock_executor):
    assert mock_executor.supports_environment("production") is True

def test_supports_environment_invalid(mock_executor):
    assert mock_executor.supports_environment("local_test") is False

def test_validation_result_structure(mock_executor, base_payload):
    val = mock_executor.validate(base_payload)
    assert hasattr(val, "is_valid")
    assert hasattr(val, "error_messages")
    assert isinstance(val.error_messages, list)

def test_execution_result_structure(mock_executor, base_payload):
    res = mock_executor.execute(base_payload)
    assert hasattr(res, "status")
    assert hasattr(res, "executed_at")
    assert hasattr(res, "attempt_id")
    assert res.executed_at is not None

def test_multiple_executions(mock_executor, base_payload):
    base_payload.sku = "SKU-OK"
    mock_executor.execute(base_payload)
    
    base_payload.attempt_id = "att_002"
    base_payload.sku = "SKU-LIMIT"
    mock_executor.execute(base_payload)
    
    assert len(mock_executor.execution_attempt_records) == 2
    assert mock_executor.execution_attempt_records[0]["status"] == "success"
    assert mock_executor.execution_attempt_records[1]["status"] == "seller_limit"
