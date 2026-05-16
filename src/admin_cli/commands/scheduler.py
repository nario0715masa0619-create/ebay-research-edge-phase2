from ..models import CliExecutionContext, CliCommandResult

class SchedulerCommands:
    def __init__(self, scheduler_service):
        self.service = scheduler_service

    def status(self, context: CliExecutionContext) -> CliCommandResult:
        summary = self.service.get_status()
        return CliCommandResult(command_path="scheduler status", summary=summary)

    def run_once(self, context: CliExecutionContext) -> CliCommandResult:
        return self.service.run_once(dry_run=context.dry_run)
