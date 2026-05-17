from typing import List, Dict, Any
from .table_renderer import TableRenderer

class NotificationCliFormatter:
    @staticmethod
    def format_recent(items: List[Dict[str, Any]]):
        headers = ["HistoryID", "Type", "Sev", "Status", "Channel", "SKU", "Title", "Time"]
        rows = [[i["history_id"], i["event_type"], i["severity"], i["status"], i["channel"], i["sku"], i["title"][:30], i["created_at"]] for i in items]
        TableRenderer.render(rows, headers, "Recent Notifications")

    @staticmethod
    def format_failed(items: List[Dict[str, Any]]):
        headers = ["HistoryID", "Type", "Status", "Channel", "Error", "Time"]
        rows = [[i["history_id"], i["event_type"], i["status"], i["channel"], i["error"][:50], i["created_at"]] for i in items]
        TableRenderer.render(rows, headers, "Failed Notifications")

    @staticmethod
    def format_channels(items: List[Dict[str, Any]]):
        headers = ["Channel", "Status", "Configured", "Type"]
        rows = [[c["channel"], c["status"], c["configured"], c["type"]] for c in items]
        TableRenderer.render(rows, headers, "Notification Channels Status")
