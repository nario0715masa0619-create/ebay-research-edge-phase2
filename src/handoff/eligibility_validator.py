from typing import List
from src.handoff.models import HandoffInput, HandoffValidationResult
from src.handoff.config import HandoffSettings
from src.ranking.models import DecisionClass

class EligibilityValidator:
    def __init__(self, settings: HandoffSettings):
        self.settings = settings

    def validate(self, input_data: HandoffInput) -> HandoffValidationResult:
        result = HandoffValidationResult()
        
        # 1. Decision Class Check
        if input_data.decision_class != DecisionClass.AUTO_LAUNCH:
            result.is_valid = False
            result.is_blocked = True
            result.block_reasons.append(f"Decision class is {input_data.decision_class.value}, not auto_launch.")
            
        # 2. Ranking / Layer Status Flags
        if input_data.execution_blocked:
            result.is_valid = False
            result.is_blocked = True
            result.block_reasons.append("Execution is explicitly blocked by Ranking layer.")
            
        if self.settings.stale_reject_enabled and (input_data.stale_flag or input_data.recheck_required):
            result.is_valid = False
            result.is_stale = True
            result.is_blocked = True
            result.block_reasons.append("Ranking or upstream data is stale. Recheck required.")
            
        # 3. Payload and Operational Guards
        if not input_data.has_valid_readiness_payload:
            result.is_valid = False
            result.is_blocked = True
            result.block_reasons.append("Invalid or missing readiness payload.")
            
        if input_data.operator_hold:
            result.is_valid = False
            result.is_blocked = True
            result.block_reasons.append("Candidate is under operator hold.")
            
        # 4. Linkage completeness (basic check)
        if not input_data.ranking_decision_id or not input_data.candidate_id:
            result.is_valid = False
            result.is_blocked = True
            result.block_reasons.append("Missing required linkage IDs.")
            
        return result
