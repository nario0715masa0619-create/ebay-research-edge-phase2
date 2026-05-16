from typing import Optional
from ..models import CliExecutionContext, CliCommandResult

class ReviewCommands:
    def __init__(self, review_service):
        self.service = review_service

    def list(self, context: CliExecutionContext, reason: Optional[str] = None) -> CliCommandResult:
        records = self.service.list_review_queue(limit=context.limit or 50, reason=reason)
        return CliCommandResult(command_path="review list", records=records)
