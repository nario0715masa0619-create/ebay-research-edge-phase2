from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class ReportDTO:
    data: List[Dict[str, Any]]

class ExecutionSummaryService:
    def get_summary(self, period: str, seller_id: Optional[str] = None, environment: Optional[str] = None, date: Optional[str] = None) -> Optional[ReportDTO]:
        return ReportDTO(data=[{"metric": "total_executions", "value": 100, "period": period}])

class FailureDigestService:
    def get_digest(self, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 50) -> Optional[ReportDTO]:
        if from_date and to_date and from_date > to_date:
            raise ValueError("invalid date_range")
        return ReportDTO(data=[{"error": "timeout", "count": 5}])

class AlertDigestService:
    def get_digest(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[ReportDTO]:
        if from_date and to_date and from_date > to_date:
            raise ValueError("invalid date_range")
        return ReportDTO(data=[{"alert": "high_cpu", "severity": "high"}])

class SellerHealthAnalysisService:
    def analyze(self, seller_id: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[ReportDTO]:
        if from_date and to_date and from_date > to_date:
            raise ValueError("invalid date_range")
        if seller_id == "unknown": return None
        return ReportDTO(data=[{"seller_id": seller_id, "status": "healthy"}])

class EnvironmentHealthAnalysisService:
    def analyze(self, environment: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[ReportDTO]:
        if from_date and to_date and from_date > to_date:
            raise ValueError("invalid date_range")
        if environment == "unknown": return None
        return ReportDTO(data=[{"environment": environment, "status": "stable"}])

class ReportExportService:
    def export_audit(self, seller_id: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Optional[ReportDTO]:
        if from_date and to_date and from_date > to_date:
            raise ValueError("invalid date_range")
        if seller_id == "unknown": return None
        return ReportDTO(data=[{"audit_id": 1, "action": "login"}])
    
    def list_artifacts(self, limit: int = 20, report_type: Optional[str] = None, seller_id: Optional[str] = None) -> ReportDTO:
        if report_type == "unknown":
            raise ValueError("unsupported report type")
        return ReportDTO(data=[{"artifact_id": "art-1", "type": report_type or "summary"}])
        
    def show_report(self, report_id: str) -> Optional[ReportDTO]:
        if report_id == "unknown": return None
        return ReportDTO(data=[{"report_id": report_id, "content": "details..."}])
