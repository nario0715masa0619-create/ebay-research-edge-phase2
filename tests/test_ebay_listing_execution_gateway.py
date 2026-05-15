import pytest
from datetime import datetime
from src.ebay.models import ProductCandidate, EbayListing
from src.listing_execution.gateway import ListingExecutionGateway
from src.listing_execution.models import ListingExecutionRequest
from src.repositories.product_candidate_repository import ProductCandidateRepository
from src.repositories.candidate_evidence_repository import CandidateEvidenceRepository
from src.repositories.job_run_repository import JobRunRepository
from src.repositories.ebay_listing_repository import EbayListingRepository

@pytest.fixture
def repos():
    return {
        "candidate": ProductCandidateRepository(),
        "evidence": CandidateEvidenceRepository(),
        "job": JobRunRepository(),
        "listing": EbayListingRepository()
    }

@pytest.fixture
def gateway(repos):
    return ListingExecutionGateway(
        candidate_repo=repos["candidate"],
        evidence_repo=repos["evidence"],
        job_repo=repos["job"],
        listing_repo=repos["listing"]
    )

def _create_ready_candidate(cid, sku="SKU-EXEC"):
    return ProductCandidate(
        candidate_id=cid,
        source_item_id=f"SRC-{cid}",
        source_platform="mercari",
        sku=sku,
        source_url="http://example.com",
        source_title="Ready Product",
        source_price_jpy=1000.0,
        pipeline_type="auto",
        decision_type="candidate",
        status="approved",
        listing_readiness_status="ready",
        publish_readiness=True,
        inventory_item_draft_json={"sku": sku, "product": {"title": "Test Item"}},
        offer_draft_json={
            "sku": sku, 
            "merchantLocationKey": "LOC1", 
            "listingPolicies": {
                "fulfillmentPolicyId": "F1", 
                "paymentPolicyId": "P1", 
                "returnPolicyId": "R1"
            }
        },
        expected_sale_price_usd=100.0
    )

# 1. listing_readiness_status != ready の候補が guard で skip / block される
def test_guard_not_ready(gateway, repos):
    candidate = _create_ready_candidate("CAND-001")
    candidate.listing_readiness_status = "blocked"
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-001"))
    assert res.execution_status == "skipped"
    assert "candidate_not_ready" in res.execution_reason_codes

# 2. manual_preban 候補が実行対象外になる
def test_guard_manual_preban(gateway, repos):
    candidate = _create_ready_candidate("CAND-002")
    candidate.pipeline_type = "manual_preban"
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-002"))
    assert res.execution_status == "skipped"
    assert "manual_preban_not_allowed" in res.execution_reason_codes

# 3. inventory_item_draft 欠損で失敗する
def test_missing_inventory_draft(gateway, repos):
    candidate = _create_ready_candidate("CAND-003")
    candidate.inventory_item_draft_json = {}
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-003"))
    assert "missing_inventory_item_draft" in res.execution_reason_codes

# 4. offer_draft 欠損で失敗する
def test_missing_offer_draft(gateway, repos):
    candidate = _create_ready_candidate("CAND-004")
    candidate.offer_draft_json = {}
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-004"))
    assert "missing_offer_draft" in res.execution_reason_codes

# 5. 正常系で createOrReplaceInventoryItem -> createOffer -> publishOffer 順に実行される
def test_successful_execution(gateway, repos):
    candidate = _create_ready_candidate("CAND-005", sku="SKU-005")
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-005"))
    assert res.execution_status == "succeeded"
    assert res.inventory_item_status in ["created", "updated"]
    assert res.offer_status == "created"
    assert res.publish_status == "published"
    assert res.listing_id is not None

# 6. publish 成功で offer_id と listing_id が EbayListing に保存される
def test_listing_persistence(gateway, repos):
    candidate = _create_ready_candidate("CAND-006", sku="SKU-006")
    repos["candidate"].upsert(candidate)
    
    gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-006"))
    
    listing = repos["listing"].get_by_sku("SKU-006")
    assert listing is not None
    assert listing.offer_id == "OFFER-SKU-006"
    assert listing.listing_id == "LISTING-OFFER-SKU-006"
    
    updated_cand = repos["candidate"].get_by_candidate_id("CAND-006")
    assert updated_cand.status == "listed"

# 7. location / policy 不足で review_required に分類される
def test_missing_policy_review(gateway, repos):
    candidate = _create_ready_candidate("CAND-007")
    candidate.offer_draft_json["listingPolicies"]["fulfillmentPolicyId"] = ""
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-007"))
    assert res.execution_status == "review_required"
    assert res.review_required_flag is True
    assert "missing_fulfillment_policy" in res.execution_reason_codes

# 8. 一時的 API エラーで retryable_error に分類される
def test_retryable_error_classification(gateway, repos):
    candidate = _create_ready_candidate("CAND-008", sku="SKU-008")
    repos["candidate"].upsert(candidate)
    
    # Mocking a failure in the API client logic via error classifier
    # In a real test, we would mock the api_client instance inside gateway.
    # For simplicity, let's just test the RetryClassifier directly or force a failure.
    
    # Let's mock the inv_executor to return a timeout error
    from unittest.mock import MagicMock
    gateway.inv_executor.execute = MagicMock(return_value={
        "success": False, "status": "failed", "error": "Connection Timeout"
    })
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-008"))
    assert res.execution_status == "retryable"
    assert res.retryable_flag is True

# 9. dry_run で API 実行せず simulated result を返す
def test_dry_run(gateway, repos):
    candidate = _create_ready_candidate("CAND-009")
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-009", dry_run=True))
    assert res.execution_status == "skipped"
    assert "dry_run_simulated" in res.execution_reason_codes

# 10. 既に listed の候補を duplicate publish しない
def test_duplicate_publish_prevention(gateway, repos):
    candidate = _create_ready_candidate("CAND-010")
    candidate.status = "listed"
    repos["candidate"].upsert(candidate)
    
    res = gateway.execute_listing_candidate(ListingExecutionRequest(candidate_id="CAND-010"))
    assert res.execution_status == "skipped"
    assert "already_listed" in res.execution_reason_codes
