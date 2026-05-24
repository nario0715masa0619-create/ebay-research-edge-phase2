from src.profitability.models import ProfitabilityInput, ProfitabilityComponentBreakdown
from src.profitability.config import ProfitabilitySettings

class CostEstimator:
    def __init__(self, settings: ProfitabilitySettings):
        self.settings = settings
        
    def estimate_costs(self, input_data: ProfitabilityInput) -> ProfitabilityComponentBreakdown:
        breakdown = ProfitabilityComponentBreakdown()
        
        # 1. Effective Source Cost
        s_price = input_data.source_price or 0.0
        s_shipping = input_data.source_shipping_cost or 0.0
        s_additional = input_data.source_additional_cost or 0.0
        
        breakdown.effective_source_cost = s_price + s_shipping + s_additional
        
        # Base Price for fee calculation
        base_price = input_data.expected_sale_price_base or 0.0
        
        # 2. Marketplace Fee (use policy or fallback)
        mp_rate = input_data.seller_policy_context.marketplace_fee_rate
        if mp_rate is None:
            mp_rate = self.settings.default_marketplace_fee_rate
            
        mp_fixed = input_data.seller_policy_context.fixed_marketplace_fee
        if mp_fixed is None:
            mp_fixed = self.settings.default_fixed_marketplace_fee
            
        breakdown.marketplace_fee = (base_price * mp_rate) + mp_fixed
        
        # 3. Payment Cost
        pay_rate = input_data.seller_policy_context.payment_fee_rate
        if pay_rate is None:
            pay_rate = self.settings.default_payment_fee_rate
            
        pay_fixed = input_data.seller_policy_context.fixed_payment_fee
        if pay_fixed is None:
            pay_fixed = self.settings.default_fixed_payment_fee
            
        breakdown.payment_cost = (base_price * pay_rate) + pay_fixed
        
        # 4. Outbound Shipping
        shipping = input_data.seller_policy_context.estimated_outbound_shipping
        if shipping is None:
            shipping = self.settings.default_outbound_shipping
        breakdown.outbound_shipping = shipping
        
        # 5. Packaging & Handling
        pkg = input_data.seller_policy_context.packaging_cost_estimate
        if pkg is None:
            pkg = self.settings.default_packaging_cost
        breakdown.packaging_cost = pkg
        
        hdl = input_data.seller_policy_context.handling_cost_estimate
        if hdl is None:
            hdl = self.settings.default_handling_cost
        breakdown.handling_cost = hdl
        
        return breakdown
