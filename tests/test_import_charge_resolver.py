import pytest
from src.import_cost.resolver import resolve_import_charges
from src.import_cost.models import (
    ImportResolutionStatus, 
    ImportConfidence, 
    ImportSourceLevel
)

def test_resolve_from_import_charges():
    # Case 1: detail に importCharges があり、そのまま採用
    detail_snap = {
        "shippingOptions": [
            {
                "importCharges": {
                    "amount": {"value": "25.50", "currency": "USD"}
                }
            }
        ]
    }
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.import_charges_estimated_total == 25.50
    assert result.import_charges_currency == "USD"
    assert result.import_resolution_status == ImportResolutionStatus.RESOLVED_EXACT
    assert result.import_confidence == ImportConfidence.HIGH
    assert result.payable_at_checkout_flag is True

def test_resolve_from_taxes_only():
    # Case 2: taxes のみあり、partial になる
    detail_snap = {
        "taxes": [
            {
                "taxPercentage": "10.0",
                "includedInPrice": False,
                "amount": {"value": "15.00", "currency": "USD"},
                "ebayCollectAndRemitTax": True
            }
        ]
    }
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.import_tax_estimated_total == 15.00
    assert result.tax_percentage == 10.0
    assert result.import_resolution_status == ImportResolutionStatus.RESOLVED_PARTIAL
    assert result.import_confidence == ImportConfidence.MEDIUM
    assert result.payable_at_checkout_flag is True

def test_resolve_fallback():
    # Case 3: import 情報なし、fallback あり
    fallback = {"rate": 0.1, "rule_id": "test_vat"}
    result = resolve_import_charges("item1", "EBAY_US", "JP", item_price=100.0, quantity=2, fallback_import_rule=fallback)
    # 100 * 0.1 * 2 = 20.0
    assert result.import_charges_estimated_total == 20.0
    assert result.import_resolution_status == ImportResolutionStatus.FALLBACK_DEFAULT
    assert result.import_confidence == ImportConfidence.LOW
    assert result.fallback_rule_used == "test_vat"

def test_resolve_unresolved():
    # Case 4: import 情報なし、fallback なし
    result = resolve_import_charges("item1", "EBAY_US", "JP")
    assert result.import_resolution_status == ImportResolutionStatus.UNRESOLVED
    assert result.import_confidence == ImportConfidence.NONE

def test_payable_at_checkout():
    # Case 5: checkout payable が true になる (taxes由来)
    detail_snap = {
        "taxes": [{"ebayCollectAndRemitTax": True, "amount": {"value": "5.0", "currency": "USD"}}]
    }
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.payable_at_checkout_flag is True

def test_payable_on_delivery_manual():
    # Case 6: (現在ロジックでは自動判定されないが、将来用プレースホルダ)
    # 現時点では getItem レスポンスから明示的に payable_on_delivery を取る項目が確定していないため
    # 基本的に unknown (None) または false となる。
    result = resolve_import_charges("item1", "EBAY_US", "JP")
    assert result.payable_on_delivery_flag is None

def test_currency_independent():
    # Case 7: 通貨が独立保持される
    detail_snap = {
        "shippingOptions": [{"importCharges": {"amount": {"value": "10.0", "currency": "EUR"}}}]
    }
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.import_charges_currency == "EUR"

def test_separation_from_shipping():
    # Case 8: shipping cost と import charges が混ざらない (Resolverの責務)
    detail_snap = {
        "shippingOptions": [
            {
                "shippingCost": {"value": "50.0", "currency": "USD"},
                "importCharges": {"amount": {"value": "10.0", "currency": "USD"}}
            }
        ]
    }
    # ShippingResolver は 50.0 を、ImportChargeResolver は 10.0 を取るはず
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.import_charges_estimated_total == 10.0
    # ここで 50.0 が足されていないことを確認
    assert result.import_charges_estimated_total != 60.0

def test_notes_and_source_level():
    # Case 9: notes と source level が正しく入る
    detail_snap = {
        "shippingOptions": [{"importCharges": {"amount": {"value": "1.0", "currency": "USD"}}}]
    }
    result = resolve_import_charges("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.import_cost_source_level == ImportSourceLevel.DETAIL_IMPORT_CHARGES
    assert any("import charges found" in note for note in result.import_notes)

def test_quantity_basis():
    # Case 10: quantity を保持する
    result = resolve_import_charges("item1", "EBAY_US", "JP", quantity=5)
    assert result.quantity_basis == 5
