from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class PayoutResolutionStatus(Enum):
    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_ESTIMATED = "resolved_estimated"
    RESOLVED_PARTIAL = "resolved_partial"
    FALLBACK_DEFAULT = "fallback_default"
    UNRESOLVED = "unresolved"

class PayoutConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class PayoutSourceLevel(Enum):
    ACCOUNT_SPECIFIC_RULE = "account_specific_rule"
    STANDARD_PRICING_MASTER = "standard_pricing_master"
    FALLBACK_MASTER = "fallback_master"
    UNRESOLVED = "unresolved"
    NONE = "none"

@dataclass
class PayoutFeeResult:
    # Aggregated Fees
    payout_fee_estimated_total: float = 0.0
    payout_fee_currency: str = ""
    payout_fee_source_level: PayoutSourceLevel = PayoutSourceLevel.NONE
    payout_resolution_status: PayoutResolutionStatus = PayoutResolutionStatus.UNRESOLVED
    payout_confidence: PayoutConfidence = PayoutConfidence.NONE

    # Breakdown
    receiving_fee_estimated_total: float = 0.0
    withdrawal_fee_estimated_total: float = 0.0
    conversion_fee_estimated_total: float = 0.0
    cross_border_fee_estimated_total: float = 0.0
    other_payout_fee_estimated_total: float = 0.0

    # Provider info
    payout_provider: str = "Payoneer"
    source_platform: str = "eBay"
    payout_method: str = "Bank Withdrawal"

    # Rule info
    fee_rule_applied: Optional[str] = None
    pricing_version_used: str = "v1"
    volume_tier_applied: Optional[str] = None

    # Flags
    conversion_required_flag: bool = False
    same_currency_withdrawal_flag: bool = False
    same_country_withdrawal_flag: bool = False

    # Payout totals
    gross_payout_amount: float = 0.0
    net_payout_estimated_amount: float = 0.0
    net_payout_currency: str = ""

    # Context & Metadata
    applied_rule_ids: List[str] = field(default_factory=list)
    applied_rule_count: int = 0
    partial_fee_components: List[str] = field(default_factory=list)
    unresolved_reason: Optional[str] = None
    payout_reason_codes: List[str] = field(default_factory=list)
    strictness: str = "balanced"

    payout_notes: List[str] = field(default_factory=list)
    payout_context_used: Dict[str, Any] = field(default_factory=dict)

    def add_note(self, note: str):
        self.payout_notes.append(note)
