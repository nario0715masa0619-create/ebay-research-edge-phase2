from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

@dataclass
class RootCauseAnalysis:
    rca_id: UUID
    learning_record_id: UUID
    problem_statement: str
    observed_symptoms: str
    primary_cause: str
    contributing_factors: str
    detection_gap: Optional[str]
    mitigation_taken: str
    resolution_summary: str
    prevention_proposal: str
    evidence_snapshot: Dict[str, Any]
    created_by: str
    created_at: datetime
