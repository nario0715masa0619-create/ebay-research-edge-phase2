import json
import io
import csv
from typing import Dict, Any, List
from datetime import datetime
from src.listing_execution.models.health_report import SellerHealthReport, EnvironmentHealthReport

class ReportExportService:
    def _to_json(self, data: Any) -> str:
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
            
        return json.dumps(data, indent=2, ensure_ascii=False, default=default_serializer)

    def _to_csv(self, headers: List[str], rows: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def export_summary_to_json(self, summary_report: Dict[str, Any]) -> str:
        return self._to_json(summary_report)

    def export_summary_to_csv(self, summary_report: Dict[str, Any]) -> str:
        headers = ["seller", "environment", "date_range_start", "date_range_end", "total_executed", "succeeded", "failed", "success_rate", "alert_count", "dry_run_count"]
        row = summary_report.copy()
        if "date_range" in row and len(row["date_range"]) == 2:
            row["date_range_start"] = row["date_range"][0]
            row["date_range_end"] = row["date_range"][1]
        return self._to_csv(headers, [row])

    def export_failure_digest_to_json(self, failure_report: Dict[str, Any]) -> str:
        return self._to_json(failure_report)

    def export_failure_digest_to_csv(self, failure_report: Dict[str, Any]) -> str:
        # A digest has complex nested data. For CSV, we can flatten recent_failures.
        recent = failure_report.get("recent_failures", [])
        headers = ["event_id", "attempt_id", "listing_id", "error_code", "error_message", "created_at"]
        return self._to_csv(headers, recent)

    def export_alert_digest_to_json(self, alert_report: Dict[str, Any]) -> str:
        return self._to_json(alert_report)

    def export_alert_digest_to_csv(self, alert_report: Dict[str, Any]) -> str:
        recent = alert_report.get("recent_alerts", [])
        headers = ["event_id", "attempt_id", "listing_id", "event_type", "created_at"]
        # details might have alert_level, but for a flat CSV we keep it simple or extract it
        for r in recent:
            if "details" in r and "alert_level" in r["details"]:
                r["alert_level"] = r["details"]["alert_level"]
        if "alert_level" not in headers:
            headers.append("alert_level")
        return self._to_csv(headers, recent)

    def export_seller_health_to_json(self, seller_report: SellerHealthReport) -> str:
        return self._to_json(seller_report)

    def export_seller_health_to_csv(self, seller_report: SellerHealthReport) -> str:
        headers = ["seller_id", "date_range_start", "date_range_end", "execution_volume", "failure_rate", "guard_rejection_count", "retry_rollback_count"]
        row = seller_report.__dict__.copy()
        if "date_range" in row and len(row["date_range"]) == 2:
            row["date_range_start"] = row["date_range"][0]
            row["date_range_end"] = row["date_range"][1]
        return self._to_csv(headers, [row])

    def export_execution_audit_to_json(self, history_list: List[Any]) -> str:
        return self._to_json(history_list)

    def export_execution_audit_to_csv(self, history_list: List[Any]) -> str:
        headers = ["event_id", "attempt_id", "listing_id", "event_type", "dry_run", "from_state", "to_state", "error_code", "created_at"]
        rows = []
        for h in history_list:
            if hasattr(h, '__dict__'):
                rows.append(h.__dict__)
            else:
                rows.append(h)
        return self._to_csv(headers, rows)
