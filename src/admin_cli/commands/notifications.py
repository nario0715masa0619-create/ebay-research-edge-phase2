from typing import Optional, List, Dict, Any
from ..models import CliExecutionContext, CliCommandResult
from ..services.notification_ops_service import NotificationOpsService

class NotificationCommands:
    def __init__(self, service: NotificationOpsService):
        self.service = service

    def recent(self, context: CliExecutionContext, limit: int = 50, severity: str = None, channel: str = None, event_type: str = None) -> CliCommandResult:
        records = self.service.get_recent(limit=limit, severity=severity, channel=channel, event_type=event_type)
        return CliCommandResult(command_path="notifications recent", records=records)

    def failed(self, context: CliExecutionContext, limit: int = 50, channel: str = None, event_type: str = None) -> CliCommandResult:
        records = self.service.get_failed(limit=limit, channel=channel, event_type=event_type)
        return CliCommandResult(command_path="notifications failed", records=records)

    def show(self, context: CliExecutionContext, history_id: str) -> CliCommandResult:
        item = self.service.get_details(history_id)
        if not item:
            return CliCommandResult(command_path="notifications show", status="error", errors=[f"History ID {history_id} not found."], exit_code=2)
        return CliCommandResult(command_path="notifications show", records=[item])

    def by_sku(self, context: CliExecutionContext, sku: str, limit: int = 20) -> CliCommandResult:
        records = self.service.get_by_sku(sku, limit=limit)
        return CliCommandResult(command_path="notifications by-sku", records=records)

    def by_event(self, context: CliExecutionContext, event_type: str, limit: int = 20) -> CliCommandResult:
        records = self.service.get_by_event(event_type, limit=limit)
        return CliCommandResult(command_path="notifications by-event", records=records)

    def resend(self, context: CliExecutionContext, history_id: str = None, event_id: str = None, channel: str = None, force: bool = False) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="notifications resend", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
            
        res = self.service.resend_notification(history_id=history_id, event_id=event_id, channel=channel, dry_run=context.dry_run, force=force)
        return CliCommandResult(command_path="notifications resend", status=res.get("status", "success"), meta=res)

    def test(self, context: CliExecutionContext, channel: str, title: str = None, summary: str = None) -> CliCommandResult:
        res = self.service.test_notification(channel, title=title, summary=summary, dry_run=context.dry_run)
        return CliCommandResult(command_path="notifications test", status=res.get("status", "success"), meta=res)

    def list_rules(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_rules()
        return CliCommandResult(command_path="notifications rules list", records=records)

    def show_rule(self, context: CliExecutionContext, rule_name: str) -> CliCommandResult:
        item = self.service.get_rule(rule_name)
        if not item:
            return CliCommandResult(command_path="notifications rules show", status="error", errors=[f"Rule {rule_name} not found."], exit_code=2)
        return CliCommandResult(command_path="notifications rules show", records=[item])

    def rules_for_event(self, context: CliExecutionContext, event_type: str, severity: str = "info") -> CliCommandResult:
        records = self.service.rule.find_rules_for_event(event_type, severity=severity)
        return CliCommandResult(command_path="notifications rules for-event", records=records)

    def channels(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_channels()
        return CliCommandResult(command_path="notifications channels", records=records)

    def stats(self, context: CliExecutionContext, hours: int = 24, event_type: str = None) -> CliCommandResult:
        item = self.service.get_stats(since_hours=hours, event_type=event_type)
        return CliCommandResult(command_path="notifications stats", records=[item])
