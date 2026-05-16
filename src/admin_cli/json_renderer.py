import json
from typing import Any, Dict
from .models import CliCommandResult

class CliJsonRenderer:
    def render(self, result: CliCommandResult) -> str:
        return json.dumps({
            "command_path": result.command_path,
            "status": result.status,
            "message": result.message,
            "summary": result.summary,
            "records": result.records,
            "errors": result.errors,
            "exit_code": result.exit_code,
            "meta": result.meta
        }, indent=2, default=str)
