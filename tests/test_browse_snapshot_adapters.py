import pytest
from src.ebay.models import EbayApiItemSummary, EbayApiItemDetail
from src.ebay.snapshot_adapters import SnapshotAdapter

def test_adapt_search_summary():
    summary = EbayApiItemSummary(
        item_id="v1|123|0",
        title="Test Item",
        price={"value": "100.00", "currency": "USD"},
        shipping_options=[{"shippingCost": {"value": "10.00", "currency": "USD"}, "shippingCostType": "FIXED"}]
    )
    
    adapter = SnapshotAdapter()
    snapshot = adapter.adapt_search_item_summary_to_snapshot(summary)
    
    assert snapshot["item_id"] == "v1|123|0"
    assert snapshot["shippingOptions"][0]["shippingCost"]["value"] == "10.00"
    assert snapshot["source"] == "api_search"

def test_adapt_detail_item():
    detail = EbayApiItemDetail(
        item_id="v1|123|0",
        title="Test Item Detail",
        price={"value": "100.00", "currency": "USD"},
        shipping_options=[{"shippingCost": {"value": "12.00", "currency": "USD"}, "type": "FIXED"}],
        taxes=[{"taxType": "VAT"}],
        return_terms={"returnShippingCostPayer": "SELLER"}
    )
    
    adapter = SnapshotAdapter()
    snapshot = adapter.adapt_detail_item_to_snapshot(detail)
    
    assert snapshot["item_id"] == "v1|123|0"
    assert snapshot["taxes"][0]["taxType"] == "VAT"
    assert snapshot["returnTerms"]["returnShippingCostPayer"] == "SELLER"
    assert snapshot["source"] == "api_detail"
