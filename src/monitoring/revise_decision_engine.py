from typing import Dict, Any, List

class ReviseDecisionEngine:
    def decide(self, 
               source_state: Dict[str, Any], 
               market_state: Dict[str, Any], 
               profit_res: Dict[str, Any],
               strictness: str = "balanced") -> Dict[str, Any]:
        
        action = "keep"
        reasons = []
        
        # Section 12: ReviseDecisionEngine 設計
        
        # 1. Check Source Availability
        if not source_state.get("source_url_alive"):
            action = "withdraw_offer"
            reasons.append("url_dead")
        elif source_state.get("latest_source_stock_status") == "out_of_stock":
            action = "set_quantity_zero"
            reasons.append("out_of_stock")
            
        # 2. Check Profitability
        updated_rate = profit_res.get("updated_expected_profit_rate", 0)
        if action == "keep" and updated_rate < 0.05: # Mock threshold
            action = "withdraw_offer"
            reasons.append("low_profitability")
            
        # 3. Check Price Changes (Simplified)
        # In real logic, compare current_marketplace_price vs target_price
        
        return {
            "revise_action": action,
            "decision_reason_codes": reasons,
            "review_required_flag": action == "review_required",
            "withdraw_recommended_flag": action == "withdraw_offer"
        }
