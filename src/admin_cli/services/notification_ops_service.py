from typing import Dict, Any, List, Optional
from .notification_history_query_service import NotificationHistoryQueryService
from .notification_resend_service import NotificationResendService
from .notification_test_service import NotificationTestService
from .notification_rule_inspect_service import NotificationRuleInspectService
from .notification_channel_inspect_service import NotificationChannelInspectService
from .notification_stats_service import NotificationStatsService

class NotificationOpsService:
    def __init__(
        self,
        query_service: NotificationHistoryQueryService,
        resend_service: NotificationResendService,
        test_service: NotificationTestService,
        rule_service: NotificationRuleInspectService,
        channel_service: NotificationChannelInspectService,
        stats_service: NotificationStatsService
    ):
        self.query = query_service
        self.resend = resend_service
        self.test = test_service
        self.rule = rule_service
        self.channel = channel_service
        self.stats = stats_service

    def get_recent(self, limit: int = 50, severity: str = None, channel: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        return self.query.list_recent(limit=limit, severity=severity, channel=channel, event_type=event_type)

    def get_failed(self, limit: int = 50, channel: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        return self.query.list_failed(limit=limit, channel=channel, event_type=event_type)

    def get_details(self, history_id: str) -> Optional[Dict[str, Any]]:
        # Handle prefix NTFH-
        id_int = int(history_id.replace("NTFH-", ""))
        return self.query.get_details(id_int)

    def get_by_sku(self, sku: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.query.list_by_sku(sku, limit=limit)

    def get_by_event(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.query.list_by_event_type(event_type, limit=limit)

    def resend_notification(self, history_id: str = None, event_id: str = None, channel: str = None, dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
        if history_id:
            id_int = int(history_id.replace("NTFH-", ""))
            return self.resend.resend_by_history_id(id_int, dry_run=dry_run, force=force)
        if event_id:
            return self.resend.resend_by_event_id(event_id, channel=channel, dry_run=dry_run, force=force)
        return {"status": "error", "message": "Either history_id or event_id must be provided."}

    def test_notification(self, channel: str, title: str = None, summary: str = None, dry_run: bool = False) -> Dict[str, Any]:
        return self.test.send_test_notification(channel, title=title or "Test Notification", summary=summary or "Test summary", dry_run=dry_run)

    def list_rules(self) -> List[Dict[str, Any]]:
        return self.rule.list_rules()

    def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        return self.rule.get_rule(rule_name)

    def list_channels(self) -> List[Dict[str, Any]]:
        return self.channel.list_channels()

    def get_stats(self, since_hours: int = 24, event_type: str = None) -> Dict[str, Any]:
        return self.stats.get_stats(since_hours=since_hours, event_type=event_type)
