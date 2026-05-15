from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class SellingFeeResolutionStatus(Enum):
    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_ESTIMATED = "resolved_estimated"
    RESOLVED_PARTIAL = "resolved_partial"
    FALLBACK_DEFAULT = "fallback_default"
    UNRESOLVED = "unresolved"

class SellingFeeConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class SellingFeeSourceLevel(Enum):
    ACCOUNT_SPECIFIC_RULE = "account_specific_rule"
    MARKETPLACE_FEE_MASTER = "marketplace_fee_master"
    FALLBACK_MASTER = "fallback_master"
    UNRESOLVED = "unresolved"
    NONE = "none"

@dataclass
class SellingFeeResult:
    # Aggregated Fees
    selling_fee_estimated_total: float = 0.0
    selling_fee_currency: str = ""
    selling_fee_source_level: SellingFeeSourceLevel = SellingFeeSourceLevel.NONE
    selling_fee_resolution_status: SellingFeeResolutionStatus = SellingFeeResolutionStatus.UNRESOLVED
    selling_fee_confidence: SellingFeeConfidence = SellingFeeConfidence.NONE

    # Breakdown
    final_value_fee_estimated_total: float = 0.0
    final_value_fee_fixed_estimated_total: float = 0.0
    insertion_fee_estimated_total: float = 0.0
    ad_fee_estimated_total: float = 0.0
    international_fee_estimated_total: float = 0.0
    regulatory_fee_estimated_total: float = 0.0
    payment_processing_fee_estimated_total: float = 0.0
    other_selling_fee_estimated_total: float = 0.0

    # Basis
    fee_basis_amount: float = 0.0
    fee_basis_currency: str = ""

    # Context
    marketplace_id: str = ""
    category_id: str = ""
    seller_store_plan: str = "basic"
    seller_performance_level: str = "top_rated"

    # Execution Metadata
    fee_rule_applied: Optional[str] = None
    applied_rule_ids: List[str] = field(default_factory=list)
    applied_rule_count: int = 0
    partial_fee_components: List[str] = field(default_factory=list)
    unresolved_reason: Optional[str] = None
    selling_reason_codes: List[str] = field(default_factory=list)
    pricing_version_used: str = "v1"
    strictness: str = "balanced"

    selling_fee_notes: List[str] = field(default_factory=list)
    selling_fee_context_used: Dict[str, Any] = field(default_factory=dict)

    def add_note(self, note: str):
        self.selling_fee_notes.append(note)
