from ..models import CliExecutionContext, CliCommandResult

class DoctorCommands:
    def __init__(self, doctor_service):
        self.service = doctor_service

    def run(self, context: CliExecutionContext) -> CliCommandResult:
        health = self.service.check_health()
        return CliCommandResult(command_path="doctor", summary=health, status=health["overall"])
