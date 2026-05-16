from typing import Dict, Any, Callable, List
import argparse
from .models import CliExecutionContext, CliCommandResult

class CommandRegistry:
    def __init__(self):
        self.commands: Dict[str, Callable[[CliExecutionContext], CliCommandResult]] = {}

    def register(self, path: str, handler: Callable[[CliExecutionContext], CliCommandResult]):
        self.commands[path] = handler

    def execute(self, path: str, context: CliExecutionContext) -> CliCommandResult:
        handler = self.commands.get(path)
        if not handler:
            return CliCommandResult(command_path=path, status="error", errors=[f"Unknown command: {path}"], exit_code=1)
        return handler(context)
