import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.listing_execution.models.execution_payload import ExecutionPayload

@pytest.fixture
def valid_payload_data():
    return {
        "listing_id": "handoff_123",
        "seller": "seller_abc",
        "sku": "SKU-999",
        "bundle_state": "standalone",
        "market_eval": {"confidence": 0.9, "competition": "low"},
        "profitability_score": 1500.0,
        "environment": "production",
        "dry_run": False,
        "attempt_id": "attempt_001"
    }

def test_execution_payload_valid(valid_payload_data):
    payload = ExecutionPayload(**valid_payload_data)
    assert payload.listing_id == "handoff_123"
    assert payload.seller == "seller_abc"
    assert payload.sku == "SKU-999"
    assert payload.bundle_state == "standalone"
    assert payload.market_eval["confidence"] == 0.9
    assert payload.profitability_score == 1500.0
    assert payload.environment == "production"
    assert payload.dry_run is False
    assert payload.attempt_id == "attempt_001"
    assert payload.timestamp is not None

def test_execution_payload_missing_required_listing_id(valid_payload_data):
    valid_payload_data.pop("listing_id")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "listing_id" in str(exc.value)

def test_execution_payload_missing_required_seller(valid_payload_data):
    valid_payload_data.pop("seller")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "seller" in str(exc.value)

def test_execution_payload_missing_required_sku(valid_payload_data):
    valid_payload_data.pop("sku")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "sku" in str(exc.value)

def test_execution_payload_missing_required_bundle_state(valid_payload_data):
    valid_payload_data.pop("bundle_state")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "bundle_state" in str(exc.value)

def test_execution_payload_missing_required_market_eval(valid_payload_data):
    valid_payload_data.pop("market_eval")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "market_eval" in str(exc.value)

def test_execution_payload_missing_required_profitability_score(valid_payload_data):
    valid_payload_data.pop("profitability_score")
    with pytest.raises(ValidationError) as exc:
        ExecutionPayload(**valid_payload_data)
    assert "profitability_score" in str(exc.value)

def test_execution_payload_context_fields_defaults():
    # Only supply required + attempt_id + environment, omit dry_run
    payload = ExecutionPayload(
        listing_id="handoff_123",
        seller="seller_abc",
        sku="SKU-999",
        bundle_state="standalone",
        market_eval={},
        profitability_score=100.0,
        environment="test",
        attempt_id="att_1"
    )
    assert payload.dry_run is False  # default
    assert isinstance(payload.timestamp, datetime)

def test_execution_payload_to_dict(valid_payload_data):
    payload = ExecutionPayload(**valid_payload_data)
    d = payload.to_dict()
    assert d["listing_id"] == "handoff_123"
    assert isinstance(d["timestamp"], str) # serialized datetime

def test_execution_payload_from_dict(valid_payload_data):
    # add ISO timestamp string to dict
    valid_payload_data["timestamp"] = datetime.now(timezone.utc).isoformat()
    payload = ExecutionPayload.from_dict(valid_payload_data)
    assert payload.listing_id == "handoff_123"
    assert isinstance(payload.timestamp, datetime)

def test_execution_payload_from_listing_factory():
    candidate_data = {
        "seller_account_id": "seller_XYZ",
        "sku": "SKU-XYZ",
        "bundle_signature": "bundled",
        "market_eval": {"valid": True},
        "profitability_score": 500.5
    }
    handoff_data = {
        "handoff_id": "handoff_XYZ"
    }
    context = {
        "environment": "production",
        "dry_run": True,
        "attempt_id": "attempt_XYZ"
    }
    
    payload = ExecutionPayload.from_listing(candidate_data, handoff_data, context)
    assert payload.listing_id == "handoff_XYZ"
    assert payload.seller == "seller_XYZ"
    assert payload.sku == "SKU-XYZ"
    assert payload.bundle_state == "bundled"
    assert payload.market_eval == {"valid": True}
    assert payload.profitability_score == 500.5
    assert payload.environment == "production"
    assert payload.dry_run is True
    assert payload.attempt_id == "attempt_XYZ"
