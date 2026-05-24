from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DecisionStatus(str, Enum):
    LAUNCH_NOW = "launch_now"
    REVIEW_REQUIRED = "review_required"
    WATCH = "watch"
    REJECT = "reject"

class ScoringStatus(str, Enum):
    SUCCESS = "success"
    INPUT_INCOMPLETE = "input_incomplete"
    INVALID_INPUT = "invalid_input"

@dataclass
class SellerPolicyContext:
    marketplace_fee_rate: Optional[float] = None
    fixed_marketplace_fee: Optional[float] = None
    payment_fee_rate: Optional[float] = None
    fixed_payment_fee: Optional[float] = None
    estimated_outbound_shipping: Optional[float] = None
    packaging_cost_estimate: Optional[float] = None
    handling_cost_estimate: Optional[float] = None

@dataclass
class ProfitabilityInput:
    candidate_id: str
    seller_account_id: str
    environment: str
    
    # Source Cost
    source_price: Optional[float] = None
    source_shipping_cost: Optional[float] = None
    source_additional_cost: Optional[float] = 0.0
    
    # Candidate & Ambiguity
    condition_family: str = "used"
    review_required: bool = False
    ambiguity_flags: List[str] = field(default_factory=list)
    special_restriction_flags: List[str] = field(default_factory=list)
    
    # Market Evaluation
    market_evaluation_id: Optional[str] = None
    expected_sale_price_low: Optional[float] = None
    expected_sale_price_base: Optional[float] = None
    expected_sale_price_high: Optional[float] = None
    market_confidence: Optional[float] = None
    comparable_count: int = 0
    competition_proxy: Optional[str] = None
    demand_proxy: Optional[str] = None
    unsafe_reasons: List[str] = field(default_factory=list)
    
    category_alignment_score: float = 1.0
    condition_alignment_score: float = 1.0
    attribute_alignment_score: float = 1.0
    
    # Policies / Fallbacks
    seller_policy_context: SellerPolicyContext = field(default_factory=SellerPolicyContext)

@dataclass
class ProfitabilityComponentBreakdown:
    effective_source_cost: float = 0.0
    marketplace_fee: float = 0.0
    payment_cost: float = 0.0
    outbound_shipping: float = 0.0
    packaging_cost: float = 0.0
    handling_cost: float = 0.0
    
    return_risk_penalty: float = 0.0
    damage_risk_penalty: float = 0.0
    authenticity_risk_penalty: float = 0.0
    restriction_risk_penalty: float = 0.0
    condition_mismatch_penalty: float = 0.0
    low_comparable_penalty: float = 0.0
    
    competition_penalty: float = 0.0
    ambiguity_penalty: float = 0.0
    
    @property
    def risk_penalty_total(self) -> float:
        return (self.return_risk_penalty + self.damage_risk_penalty + 
                self.authenticity_risk_penalty + self.restriction_risk_penalty + 
                self.condition_mismatch_penalty + self.low_comparable_penalty)
                
    @property
    def total_cost_and_penalty(self) -> float:
        return (self.effective_source_cost + self.marketplace_fee + self.payment_cost + 
                self.outbound_shipping + self.packaging_cost + self.handling_cost + 
                self.risk_penalty_total + self.competition_penalty + self.ambiguity_penalty)

@dataclass
class ProfitabilityResult:
    profitability_score_id: str
    candidate_id: str
    market_evaluation_id: Optional[str]
    scoring_status: ScoringStatus
    
    expected_sale_price_low: Optional[float]
    expected_sale_price_base: Optional[float]
    expected_sale_price_high: Optional[float]
    
    components: ProfitabilityComponentBreakdown
    
    expected_net_profit: float
    expected_margin: float
    expected_roi: float
    
    confidence_multiplier: float
    confidence_adjusted_profit: float
    profitability_score: float
    
    decision_status: DecisionStatus
    decision_reason: str
    review_required: bool
    
    unsafe_reasons: List[str]
    explanation_lines: List[str]
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
