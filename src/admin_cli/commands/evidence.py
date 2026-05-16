from ..models import CliExecutionContext, CliCommandResult

class EvidenceCommands:
    def __init__(self, evidence_service):
        self.service = evidence_service

    def list(self, context: CliExecutionContext, candidate_id: str) -> CliCommandResult:
        records = self.service.list_by_candidate(candidate_id)
        return CliCommandResult(command_path="evidence list", records=records)

    def show(self, context: CliExecutionContext, evidence_id: str) -> CliCommandResult:
        detail = self.service.get_detail(evidence_id)
        if not detail:
            return CliCommandResult(command_path="evidence show", status="error", errors=[f"Evidence {evidence_id} not found"], exit_code=2)
        return CliCommandResult(command_path="evidence show", summary=detail)
