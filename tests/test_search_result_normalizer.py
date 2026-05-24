import pytest
from src.market_eval.search_result_normalizer import SearchResultNormalizer

def test_normalizer_find_completed_items_format():
    raw_data = [
        {
            "itemId": ["12345"],
            "title": ["Test Item"],
            "primaryCategory": [{"categoryName": ["Electronics"]}],
            "viewItemURL": ["http://ebay.com/itm/12345"],
            "sellingStatus": [
                {
                    "currentPrice": [{"@currencyId": "USD", "__value__": "150.50"}],
                    "sellingState": ["EndedWithSales"]
                }
            ],
            "shippingInfo": [
                {
                    "shippingServiceCost": [{"@currencyId": "USD", "__value__": "10.0"}]
                }
            ],
            "condition": [{"conditionDisplayName": ["Used"]}]
        }
    ]
    
    normalizer = SearchResultNormalizer()
    snapshots = normalizer.normalize_items(raw_data)
    
    assert len(snapshots) == 1
    snap = snapshots[0]
    assert snap.listing_id == "12345"
    assert snap.title == "Test Item"
    assert snap.price == 150.50
    assert snap.currency == "USD"
    assert snap.shipping_price == 10.0
    assert snap.is_sold is True
    assert snap.condition == "Used"
    assert snap.category_path == "Electronics"
    assert snap.listing_url == "http://ebay.com/itm/12345"

def test_normalizer_alternative_mock_format():
    raw_data = [
        {
            "itemId": "9999",
            "title": "Mock Item",
            "price": {"value": "99.99", "currency": "JPY"},
            "condition": "USED_GOOD",
            "categories": [{"categoryName": "Games"}],
            "itemWebUrl": "http://ebay.com/itm/9999"
        }
    ]
    normalizer = SearchResultNormalizer()
    snapshots = normalizer.normalize_items(raw_data)
    
    assert len(snapshots) == 1
    snap = snapshots[0]
    assert snap.listing_id == "9999"
    assert snap.price == 99.99
    assert snap.currency == "JPY"
    assert snap.is_sold is True # default assumed true for price > 0 when missing sellingState
    assert snap.condition == "USED_GOOD"
    assert "Games" in snap.category_path
    assert snap.listing_url == "http://ebay.com/itm/9999"
