from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class ShippingResolutionStatus(Enum):
    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_ESTIMATED = "resolved_estimated"
    RESOLVED_PARTIAL = "resolved_partial"
    FALLBACK_DEFAULT = "fallback_default"
    UNRESOLVED = "unresolved"

class ShippingConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class ShippingSourceLevel(Enum):
    SEARCH = "search"
    DETAIL = "detail"
    FALLBACK = "fallback"
    NONE = "none"

@dataclass
class ShippingResult:
    shipping_estimated_total: float = 0.0
    shipping_currency: str = ""
    shipping_source_level: ShippingSourceLevel = ShippingSourceLevel.NONE
    shipping_cost_type: str = ""  # e.g., FIXED, CALCULATED
    shipping_resolution_status: ShippingResolutionStatus = ShippingResolutionStatus.UNRESOLVED
    shipping_confidence: ShippingConfidence = ShippingConfidence.NONE
    vat_included_flag: bool = False
    taxes_included_flag: bool = False
    import_charges_included_flag: bool = False
    import_charges_estimated_total: float = 0.0
    return_shipping_risk_flag: bool = False  # True if seller pays for return shipping (risk for seller, but here maybe it means risk for buyer if not covered?)
    # Re-reading prompt: "return_shipping_risk_flag: 返品送料リスク有無" 
    # Usually risk exists if buyer pays. Let's clarify in implementation.
    quantity_basis: int = 1
    delivery_context_used: Dict[str, Any] = field(default_factory=dict)
    selected_option_summary: str = ""
    raw_shipping_options_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def add_note(self, note: str):
        self.notes.append(note)
