from typing import List, Optional, Dict, Any
from sqlalchemy import text
from src.db.session import SessionManager
from src.auth.token_service import EbayTokenService
from src.orchestrator.orchestrator import ScheduledOrchestrator

class DoctorService:
    def __init__(self, session_manager: SessionManager, token_service: EbayTokenService, orchestrator: ScheduledOrchestrator, notification_dispatcher=None):
        self.session_manager = session_manager
        self.token_service = token_service
        self.orchestrator = orchestrator
        self.notification_dispatcher = notification_dispatcher

    def check_health(self) -> Dict[str, Any]:
        results = {
            "db": self._check_db(),
            "auth": self._check_auth(),
            "scheduler": self._check_scheduler(),
            "overall": "ok"
        }
        
        if any(v["status"] != "ok" for v in results.values() if isinstance(v, dict)):
            results["overall"] = "fail" if any(v["status"] == "fail" for v in results.values() if isinstance(v, dict)) else "warning"
            
            # Notify if dispatcher is available
            if hasattr(self, "notification_dispatcher") and self.notification_dispatcher:
                from src.notification.models import NotificationEvent
                event = NotificationEvent(
                    event_type="doctor_check_failed",
                    source_layer="admin_cli",
                    source_component="DoctorService",
                    title=f"System Health Check: {results['overall'].upper()}",
                    summary="One or more health checks failed.",
                    severity="error" if results["overall"] == "fail" else "warning",
                    priority="high"
                )
                self.notification_dispatcher.notify(event)
                
        return results

    def _check_db(self) -> Dict[str, Any]:
        try:
            with self.session_manager.session() as session:
                session.execute(text("SELECT 1"))
            return {"status": "ok", "message": "Connection successful."}
        except Exception as e:
            return {"status": "fail", "message": str(e)}

    def _check_auth(self) -> Dict[str, Any]:
        # Minimal check: do we have credentials configured?
        creds = self.token_service.credentials
        if not creds.client_id:
            return {"status": "fail", "message": "EBAY_CLIENT_ID missing."}
        return {"status": "ok", "message": "Credentials found (masked)."}

    def _check_scheduler(self) -> Dict[str, Any]:
        engine = self.orchestrator.engine
        jobs = engine.registry.list_enabled_jobs()
        if not jobs:
            return {"status": "warning", "message": "No jobs registered."}
        return {"status": "ok", "message": f"{len(jobs)} jobs registered."}
