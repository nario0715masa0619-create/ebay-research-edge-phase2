import pytest
from src.listing_readiness.services.readiness_checker import ReadinessChecker

# Fixtures for the 5 patterns
@pytest.fixture
def all_ok():
    return {
        "candidate": {"sku": "SKU-1", "title": "Test Product", "profitability_score": 100.0},
        "seller": {"is_active": True},
        "handoff": {"handoff_status": "validated"}
    }

@pytest.fixture
def seller_invalid(all_ok):
    data = all_ok.copy()
    data["seller"] = {"is_active": False}
    return data

@pytest.fixture
def sku_missing(all_ok):
    data = all_ok.copy()
    data["candidate"] = {"sku": "", "title": "Test Product", "profitability_score": 100.0}
    return data

@pytest.fixture
def pricing_conflict(all_ok):
    data = all_ok.copy()
    data["candidate"]["profitability_score"] = -10.0
    return data

@pytest.fixture
def state_pending(all_ok):
    data = all_ok.copy()
    data["handoff"]["handoff_status"] = "pending"
    return data

def test_readiness_all_ok(all_ok):
    checker = ReadinessChecker()
    res = checker.check_readiness(all_ok["candidate"], all_ok["seller"], all_ok["handoff"])
    assert res.is_ready is True
    assert res.readiness_score == 100.0
    assert len(res.readiness_reasons) == 0

def test_readiness_seller_invalid(seller_invalid):
    checker = ReadinessChecker()
    res = checker.check_readiness(seller_invalid["candidate"], seller_invalid["seller"], seller_invalid["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("seller_invalid" in r for r in res.readiness_reasons)

def test_readiness_sku_missing(sku_missing):
    checker = ReadinessChecker()
    res = checker.check_readiness(sku_missing["candidate"], sku_missing["seller"], sku_missing["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("sku_missing" in r for r in res.readiness_reasons)

def test_readiness_content_incomplete(all_ok):
    data = all_ok.copy()
    data["candidate"]["title"] = "" # missing title
    checker = ReadinessChecker()
    res = checker.check_readiness(data["candidate"], data["seller"], data["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("content_incomplete" in r for r in res.readiness_reasons)

def test_readiness_pricing_conflict(pricing_conflict):
    checker = ReadinessChecker()
    res = checker.check_readiness(pricing_conflict["candidate"], pricing_conflict["seller"], pricing_conflict["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("pricing_conflict" in r for r in res.readiness_reasons)
    
def test_readiness_pricing_zero(pricing_conflict):
    pricing_conflict["candidate"]["profitability_score"] = 0.0
    checker = ReadinessChecker()
    res = checker.check_readiness(pricing_conflict["candidate"], pricing_conflict["seller"], pricing_conflict["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("pricing_conflict" in r for r in res.readiness_reasons)

def test_readiness_state_pending(state_pending):
    checker = ReadinessChecker()
    res = checker.check_readiness(state_pending["candidate"], state_pending["seller"], state_pending["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("state_pending" in r for r in res.readiness_reasons)

def test_readiness_state_deferred(state_pending):
    state_pending["handoff"]["handoff_status"] = "deferred"
    checker = ReadinessChecker()
    res = checker.check_readiness(state_pending["candidate"], state_pending["seller"], state_pending["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("state_pending" in r for r in res.readiness_reasons)

def test_readiness_state_failed(state_pending):
    state_pending["handoff"]["handoff_status"] = "failed"
    checker = ReadinessChecker()
    res = checker.check_readiness(state_pending["candidate"], state_pending["seller"], state_pending["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("state_pending" in r for r in res.readiness_reasons)

def test_readiness_state_rejected(state_pending):
    state_pending["handoff"]["handoff_status"] = "rejected"
    checker = ReadinessChecker()
    res = checker.check_readiness(state_pending["candidate"], state_pending["seller"], state_pending["handoff"])
    assert res.is_ready is False
    assert res.readiness_score == 80.0
    assert any("state_pending" in r for r in res.readiness_reasons)

def test_readiness_multiple_failures(all_ok):
    # Simulate seller invalid, sku missing, and pending state
    data = all_ok.copy()
    data["seller"]["is_active"] = False
    data["candidate"]["sku"] = ""
    data["handoff"]["handoff_status"] = "pending"
    
    checker = ReadinessChecker()
    res = checker.check_readiness(data["candidate"], data["seller"], data["handoff"])
    assert res.is_ready is False
    # 3 failures * 20.0 = 60.0 score penalty => score 40.0
    assert res.readiness_score == 40.0
    assert len(res.readiness_reasons) == 3
    
    assert any("seller_invalid" in r for r in res.readiness_reasons)
    assert any("sku_missing" in r for r in res.readiness_reasons)
    assert any("state_pending" in r for r in res.readiness_reasons)

def test_readiness_timestamp_exists(all_ok):
    checker = ReadinessChecker()
    res = checker.check_readiness(all_ok["candidate"], all_ok["seller"], all_ok["handoff"])
    assert res.readiness_timestamp is not None

def test_readiness_null_candidate_data():
    checker = ReadinessChecker()
    res = checker.check_readiness({}, {"is_active": True}, {"handoff_status": "validated"})
    assert res.is_ready is False
    assert res.readiness_score == 40.0 # sku missing, content incomplete, and pricing conflict (0.0)
    assert len(res.readiness_reasons) == 3

def test_readiness_null_seller_data():
    checker = ReadinessChecker()
    res = checker.check_readiness({"sku": "S", "title": "T", "profitability_score": 10}, {}, {"handoff_status": "validated"})
    assert res.is_ready is False
    assert res.readiness_score == 80.0 # seller invalid

def test_readiness_null_handoff_data():
    checker = ReadinessChecker()
    res = checker.check_readiness({"sku": "S", "title": "T", "profitability_score": 10}, {"is_active": True}, {})
    assert res.is_ready is True
    assert res.readiness_score == 100.0 # Empty handoff_status falls through if not in the restricted list
