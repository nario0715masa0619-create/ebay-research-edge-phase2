from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class TotalCostResolutionStatus(Enum):
    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_ESTIMATED = "resolved_estimated"
    RESOLVED_PARTIAL = "resolved_partial"
    FALLBACK_DEFAULT = "fallback_default"
    UNRESOLVED = "unresolved"

class TotalCostConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class TotalCostSourceLevel(Enum):
    FULL_AGGREGATION = "full_aggregation"
    PARTIAL_AGGREGATION = "partial_aggregation"
    FALLBACK_HEAVY = "fallback_heavy"
    UNRESOLVED = "unresolved"
    NONE = "none"

@dataclass
class TotalCostResult:
    # Aggregated Status
    total_cost_estimated: float = 0.0
    total_cost_currency: str = "USD"
    total_cost_source_level: TotalCostSourceLevel = TotalCostSourceLevel.NONE
    total_cost_resolution_status: TotalCostResolutionStatus = TotalCostResolutionStatus.UNRESOLVED
    total_cost_confidence: TotalCostConfidence = TotalCostConfidence.NONE

    # Revenue metrics
    gross_checkout_total: float = 0.0
    gross_sale_ex_tax: float = 0.0

    # Procurement & Landed Cost
    procurement_item_cost_total: float = 0.0
    shipping_cost_total: float = 0.0
    import_cost_total: float = 0.0
    landed_procurement_cost_total: float = 0.0

    # Fee layers
    selling_cost_total: float = 0.0
    payout_cost_total: float = 0.0
    additional_fixed_cost_total: float = 0.0
    additional_variable_cost_total: float = 0.0

    # Profit metrics
    profit_before_payout_fee: float = 0.0
    final_profit_after_all_costs: float = 0.0
    estimated_margin_rate: Optional[float] = None
    estimated_roi: Optional[float] = None

    # Quality indicators
    unresolved_components: List[str] = field(default_factory=list)
    fallback_components: List[str] = field(default_factory=list)
    partial_components: List[str] = field(default_factory=list)

    # Context & Metadata
    total_cost_notes: List[str] = field(default_factory=list)
    total_cost_context_used: Dict[str, Any] = field(default_factory=dict)
    tax_handling_mode: str = "tax_excluded_from_profit_base"

    def add_note(self, note: str):
        self.total_cost_notes.append(note)
