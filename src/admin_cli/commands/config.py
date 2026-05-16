from ..models import CliExecutionContext, CliCommandResult

class ConfigCommands:
    def __init__(self, config_service):
        self.service = config_service

    def validate(self, context: CliExecutionContext) -> CliCommandResult:
        report = self.service.validate()
        records = [{"key": k, "status": v["status"], "message": v["message"]} for k, v in report["checks"].items()]
        return CliCommandResult(command_path="config validate", summary={"status": report["status"]}, records=records)
