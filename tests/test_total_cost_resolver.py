import pytest
from dataclasses import dataclass
from src.total_cost.resolver import resolve_total_cost
from src.total_cost.models import (
    TotalCostResolutionStatus,
    TotalCostConfidence,
    TotalCostSourceLevel
)

@dataclass
class MockResult:
    shipping_estimated_total: float = 0.0
    shipping_resolution_status: str = "resolved_estimated"
    import_charges_estimated_total: float = 0.0
    import_resolution_status: str = "resolved_estimated"
    selling_fee_estimated_total: float = 0.0
    selling_fee_resolution_status: str = "resolved_estimated"
    payout_fee_estimated_total: float = 0.0
    payout_resolution_status: str = "resolved_estimated"

def test_full_aggregation_success():
    # 1. 4 resolver が揃った状態で総コストと利益が正しく計算される
    shipping = MockResult(shipping_estimated_total=20.0)
    import_ch = MockResult(import_charges_estimated_total=10.0)
    selling = MockResult(selling_fee_estimated_total=15.0)
    payout = MockResult(payout_fee_estimated_total=2.0)
    
    # Gross sale ex tax: 100 + 10 = 110
    # Landed cost: (50*1) + 20 + 10 = 80
    # Total cost: 80 + 15 + 2 = 97
    # Profit: 110 - 97 = 13
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        buyer_charged_shipping=10.0,
        shipping_result=shipping,
        import_result=import_ch,
        selling_fee_result=selling,
        payout_fee_result=payout
    )
    
    assert result.total_cost_estimated == 97.0
    assert result.final_profit_after_all_costs == 13.0
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.RESOLVED_ESTIMATED
    assert result.total_cost_confidence == TotalCostConfidence.HIGH

def test_payout_missing_partial():
    # 2. payout 未入力でも profit_before_payout_fee が返る
    shipping = MockResult(shipping_estimated_total=20.0)
    import_ch = MockResult(import_charges_estimated_total=10.0)
    selling = MockResult(selling_fee_estimated_total=15.0)
    
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        shipping_result=shipping,
        import_result=import_ch,
        selling_fee_result=selling,
        payout_fee_result=None # Missing -> RESOLVED_PARTIAL
    )
    
    assert result.profit_before_payout_fee == 5.0
    # Wait, Gross Sale ex tax = 100. Landed = 80. Selling = 15. 100-95 = 5.
    assert result.final_profit_after_all_costs == 5.0
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.RESOLVED_PARTIAL
    assert "payout_fee" in result.partial_components

def test_strict_mode_unresolved_shipping():
    # 3. strict モードで shipping 欠落時に unresolved になる
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        shipping_result=None, # Missing
        strictness="strict"
    )
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.UNRESOLVED

def test_strict_mode_unresolved_selling():
    # 4. strict モードで selling fee 欠落時に unresolved になる
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        selling_fee_result=None, # Missing
        strictness="strict"
    )
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.UNRESOLVED

def test_fallback_component_status():
    # 5. fallback component を含むと status が fallback 系になる
    shipping = MockResult(shipping_estimated_total=20.0, shipping_resolution_status="fallback_default")
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        shipping_result=shipping,
        import_result=MockResult(),
        selling_fee_result=MockResult(),
        payout_fee_result=MockResult() # Provide to avoid PARTIAL
    )
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.FALLBACK_DEFAULT
    assert "shipping" in result.fallback_components

def test_partial_component_status():
    # 6. partial component を含むと partial になる
    import_ch = MockResult(import_charges_estimated_total=10.0, import_resolution_status="resolved_partial")
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        shipping_result=MockResult(),
        import_result=import_ch,
        selling_fee_result=MockResult(),
        payout_fee_result=MockResult() # Provide to avoid additional PARTIAL
    )
    assert result.total_cost_resolution_status == TotalCostResolutionStatus.RESOLVED_PARTIAL
    assert "import" in result.partial_components

def test_tax_handling():
    # 7. tax が gross_checkout_total には入るが profit base には入らない
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        collected_tax=10.0,
        shipping_result=MockResult(),
        import_result=MockResult(),
        selling_fee_result=MockResult(),
        payout_fee_result=MockResult()
    )
    assert result.gross_checkout_total == 110.0
    assert result.gross_sale_ex_tax == 100.0
    # Final profit should be based on 100.0 - costs
    assert result.final_profit_after_all_costs == 50.0 # 100 - (50+0+0+0)

def test_roi_calculation():
    # 8. ROI が landed_procurement_cost_total ベースで正しく計算される
    shipping = MockResult(shipping_estimated_total=10.0)
    import_ch = MockResult(import_charges_estimated_total=10.0)
    result = resolve_total_cost(
        procurement_item_cost=50.0,
        sale_item_price=100.0,
        shipping_result=shipping,
        import_result=import_ch,
        selling_fee_result=MockResult(),
        payout_fee_result=MockResult()
    )
    # Landed: 50+10+10=70. Profit: 100-70=30. ROI: 30/70=0.428...
    assert pytest.approx(result.estimated_roi, 0.001) == 0.4285

def test_negative_profit():
    # 9. negative profit でも正しく返る
    result = resolve_total_cost(
        procurement_item_cost=150.0,
        sale_item_price=100.0,
        shipping_result=MockResult(),
        import_result=MockResult(),
        selling_fee_result=MockResult(),
        payout_fee_result=MockResult()
    )
    assert result.final_profit_after_all_costs == -50.0
    assert result.estimated_margin_rate == -0.5

def test_notes_and_components_tracking():
    # 10. notes / unresolved_components / fallback_components が正しく入る
    result = resolve_total_cost(
        procurement_item_cost=0.0, # Missing procurement
        sale_item_price=100.0,
        shipping_result=None,
        selling_fee_result=None
    )
    assert "procurement" in result.unresolved_components
    assert "shipping" in result.unresolved_components
    assert "selling_fee" in result.unresolved_components
    assert any("missing procurement cost" in n for n in result.total_cost_notes)
