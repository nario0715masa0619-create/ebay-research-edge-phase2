from ..models import CliExecutionContext, CliCommandResult

class JobRunCommands:
    def __init__(self, jobrun_service):
        self.service = jobrun_service

    def recent(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_recent(limit=context.limit or 10)
        return CliCommandResult(command_path="jobruns recent", records=records)

    def show(self, context: CliExecutionContext, run_id: str) -> CliCommandResult:
        detail = self.service.get_detail(run_id)
        if not detail:
            return CliCommandResult(command_path="jobruns show", status="error", errors=[f"Run {run_id} not found"], exit_code=2)
        return CliCommandResult(command_path="jobruns show", summary=detail)
