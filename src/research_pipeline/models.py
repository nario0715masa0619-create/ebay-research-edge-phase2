from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class CandidateBuildRequest:
    source_item_id: str
    run_id: Optional[str] = None
    force_rebuild: bool = False
    strictness: str = "balanced"
    rule_version: str = "v1"
    scoring_profile: str = "balanced"
    marketplace_id: str = "EBAY_US"
    delivery_country: str = "JP"
    zip_code: Optional[str] = None
    quantity: int = 1

@dataclass
class CandidateBuildResult:
    source_item_id: str
    candidate_id: Optional[str] = None
    sku: Optional[str] = None
    pipeline_type: str = "auto"
    decision_type: str = "excluded"
    status: str = "collected"
    auto_listable: bool = False
    exclude_reason: Optional[str] = None
    review_reason: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    success_flag: bool = False

@dataclass
class ResearchPipelineResult:
    run_id: str
    processed_count: int = 0
    success_count: int = 0
    excluded_count: int = 0
    review_count: int = 0
    candidate_count: int = 0
    error_count: int = 0
    error_summary: List[str] = field(default_factory=list)
