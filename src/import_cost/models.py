from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class ImportResolutionStatus(Enum):
    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_ESTIMATED = "resolved_estimated"
    RESOLVED_PARTIAL = "resolved_partial"
    FALLBACK_DEFAULT = "fallback_default"
    UNRESOLVED = "unresolved"

class ImportConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class ImportSourceLevel(Enum):
    DETAIL_IMPORT_CHARGES = "detail_import_charges"
    DETAIL_TAXES = "detail_taxes"
    FALLBACK_MASTER = "fallback_master"
    UNRESOLVED = "unresolved"
    NONE = "none"

@dataclass
class ImportChargeResult:
    # Aggregated Costs
    import_charges_estimated_total: float = 0.0
    import_charges_currency: str = ""
    import_cost_source_level: ImportSourceLevel = ImportSourceLevel.NONE
    import_resolution_status: ImportResolutionStatus = ImportResolutionStatus.UNRESOLVED
    import_confidence: ImportConfidence = ImportConfidence.NONE

    # Breakdown (Estimates)
    import_duty_estimated_total: float = 0.0
    import_tax_estimated_total: float = 0.0
    import_brokerage_estimated_total: float = 0.0
    import_other_estimated_total: float = 0.0

    # Flags
    import_charges_included_flag: bool = False
    payable_at_checkout_flag: Optional[bool] = None  # None = Unknown
    payable_on_delivery_flag: Optional[bool] = None

    # Tax Information
    tax_present_flag: bool = False
    tax_included_in_price_flag: Optional[bool] = None
    shipping_taxed_flag: Optional[bool] = None
    tax_percentage: Optional[float] = None

    # Context & Metadata
    quantity_basis: int = 1
    delivery_context_used: Dict[str, Any] = field(default_factory=dict)
    raw_import_snapshot: Dict[str, Any] = field(default_factory=dict)
    import_notes: List[str] = field(default_factory=list)
    fallback_rule_used: Optional[str] = None

    def add_note(self, note: str):
        self.import_notes.append(note)
