from typing import Optional
from ..models import CliExecutionContext, CliCommandResult

class CandidateCommands:
    def __init__(self, candidate_service):
        self.service = candidate_service

    def list(self, context: CliExecutionContext, status: Optional[str] = None) -> CliCommandResult:
        records = self.service.list_candidates(status=status, limit=context.limit or 20)
        return CliCommandResult(command_path="candidates list", records=records)

    def show(self, context: CliExecutionContext, sku: str) -> CliCommandResult:
        detail = self.service.get_candidate_detail(sku)
        if not detail:
            return CliCommandResult(command_path="candidates show", status="error", errors=[f"SKU {sku} not found"], exit_code=2)
        return CliCommandResult(command_path="candidates show", summary=detail)
