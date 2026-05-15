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

class CarrierNormalized(Enum):
    FEDEX = "FEDEX"
    POSTAL = "POSTAL"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class CarrierFilterStatus(Enum):
    ALLOWED_CARRIER_SELECTED = "allowed_carrier_selected"
    NO_ALLOWED_CARRIER_FOUND = "no_allowed_carrier_found"
    ONLY_DISALLOWED_CARRIERS_FOUND = "only_disallowed_carriers_found"
    CARRIER_UNKNOWN_NEEDS_DETAIL = "carrier_unknown_needs_detail"
    CARRIER_UNKNOWN_AFTER_DETAIL = "carrier_unknown_after_detail"
    FALLBACK_USED_DUE_TO_NO_ALLOWED_CARRIER = "fallback_used_due_to_no_allowed_carrier"
    UNRESOLVED_NO_ALLOWED_CARRIER = "unresolved_no_allowed_carrier"
    NONE = "none"

@dataclass
class ShippingResult:
    shipping_estimated_total: float = 0.0
    shipping_currency: str = ""
    shipping_source_level: ShippingSourceLevel = ShippingSourceLevel.NONE
    shipping_cost_type: str = ""  # e.g., FIXED, CALCULATED
    shipping_resolution_status: ShippingResolutionStatus = ShippingResolutionStatus.UNRESOLVED
    shipping_confidence: ShippingConfidence = ShippingConfidence.NONE
    
    # Carrier specific fields
    service_name_raw: str = ""
    carrier_normalized: CarrierNormalized = CarrierNormalized.UNKNOWN
    carrier_allowed_flag: bool = False
    carrier_filter_status: CarrierFilterStatus = CarrierFilterStatus.NONE
    
    vat_included_flag: Optional[bool] = None
    taxes_included_flag: Optional[bool] = None
    import_charges_included_flag: bool = False
    import_charges_estimated_total: float = 0.0
    return_shipping_risk_flag: bool = False  # True if seller pays for return shipping
    quantity_basis: int = 1
    delivery_context_used: Dict[str, Any] = field(default_factory=dict)
    selected_option_summary: str = ""
    raw_shipping_options_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # Pipeline metadata
    detail_fetch_attempted: bool = False
    detail_fetch_succeeded: bool = False
    detail_fetch_reasons: List[str] = field(default_factory=list)
    pipeline_mode: str = "balanced"

    def add_note(self, note: str):
        self.notes.append(note)
