from ..models import CliExecutionContext, CliCommandResult

class EventCommands:
    def __init__(self, event_service):
        self.service = event_service

    def recent(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_recent(limit=context.limit or 20)
        return CliCommandResult(command_path="events recent", records=records)

    def show(self, context: CliExecutionContext, event_id: str) -> CliCommandResult:
        detail = self.service.get_detail(event_id)
        if not detail:
            return CliCommandResult(command_path="events show", status="error", errors=[f"Event {event_id} not found"], exit_code=2)
        return CliCommandResult(command_path="events show", summary=detail)
