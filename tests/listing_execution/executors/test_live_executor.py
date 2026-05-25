import pytest
from datetime import datetime, timezone
from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.gateways.ebay_api_gateway import EBayApiGateway
from src.listing_execution.executors.live_executor import LiveExecutor

@pytest.fixture
def api_gateway():
    return EBayApiGateway()

@pytest.fixture
def live_executor(api_gateway):
    return LiveExecutor(
        allowed_environments=["sandbox", "production"],
        allowed_sellers=["seller_A"],
        api_gateway=api_gateway
    )

@pytest.fixture
def valid_credentials():
    return {"auth_token": "valid_token"}

@pytest.fixture
def sample_payload():
    return ExecutionPayload(
        listing_id="lst_001",
        seller="seller_A",
        sku="sku_123",
        bundle_state="none",
        market_eval={},
        profitability_score=95.0,
        environment="sandbox",
        dry_run=False,
        attempt_id="att_001",
        timestamp=datetime.now(timezone.utc)
    )

def test_supports_environment(live_executor):
    assert live_executor.supports_environment("sandbox") is True
    assert live_executor.supports_environment("invalid_env") is False

def test_validate_success(live_executor, sample_payload, valid_credentials):
    result = live_executor.validate(sample_payload, valid_credentials)
    assert result.is_valid is True

def test_validate_invalid_environment(live_executor, sample_payload, valid_credentials):
    sample_payload.environment = "unknown_env"
    result = live_executor.validate(sample_payload, valid_credentials)
    assert result.is_valid is False
    assert "Environment" in result.error_messages[0]

def test_validate_invalid_seller(live_executor, sample_payload, valid_credentials):
    sample_payload.seller = "unauthorized_seller"
    result = live_executor.validate(sample_payload, valid_credentials)
    assert result.is_valid is False
    assert "Seller" in result.error_messages[0]

def test_validate_invalid_credentials(live_executor, sample_payload):
    result = live_executor.validate(sample_payload, {})
    assert result.is_valid is False
    assert "credentials" in result.error_messages[0]

def test_execute_dry_run(live_executor, sample_payload, valid_credentials):
    sample_payload.dry_run = True
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "success"
    assert "Dry run" in result.error_reason

def test_execute_missing_credentials(live_executor, sample_payload):
    result = live_executor.execute(sample_payload, None)
    assert result.status == "failed"
    assert "Missing credentials" in result.error_reason

def test_execute_success(live_executor, sample_payload, valid_credentials):
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "success"
    assert result.listing_id == "lst_sku_123"

def test_execute_timeout(live_executor, sample_payload, valid_credentials):
    sample_payload.sku = "item_timeout"
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "failed"
    assert "Timeout" in result.error_reason

def test_execute_ratelimit(live_executor, sample_payload, valid_credentials):
    sample_payload.sku = "item_ratelimit"
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "failed"
    assert "Rate Limit" in result.error_reason

def test_execute_invalid_request(live_executor, sample_payload, valid_credentials):
    sample_payload.sku = "item_invalid"
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "failed"
    assert "Invalid Request" in result.error_reason

def test_execute_publish_timeout(live_executor, sample_payload, valid_credentials):
    sample_payload.sku = "item_publish_timeout"
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.status == "failed"
    assert "Timeout" in result.error_reason

def test_api_gateway_validate_credentials(api_gateway, valid_credentials):
    assert api_gateway.validate_credentials(valid_credentials) is True
    assert api_gateway.validate_credentials({}) is False
    assert api_gateway.validate_credentials({"auth_token": ""}) is False

def test_api_gateway_create_or_replace_inventory_item(api_gateway, valid_credentials):
    assert api_gateway.create_or_replace_inventory_item("sku1", {}, valid_credentials) is True

def test_api_gateway_create_offer(api_gateway, valid_credentials):
    offer_id = api_gateway.create_offer("sku1", "EBAY_US", valid_credentials)
    assert offer_id == "offer_sku1"

def test_api_gateway_publish_offer(api_gateway, valid_credentials):
    response = api_gateway.publish_offer("offer_sku1", valid_credentials)
    assert response.listing_id == "lst_sku1"
    assert response.status == "published"

def test_execute_integration_with_execution_attempt(live_executor, sample_payload, valid_credentials):
    # Testing that it returns the expected ExecutionResult
    # that Phase H's execution_attempt would persist.
    result = live_executor.execute(sample_payload, valid_credentials)
    assert result.attempt_id == sample_payload.attempt_id
    assert result.executed_at is not None
