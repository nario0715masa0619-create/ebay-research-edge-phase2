from typing import Dict, Any, Optional
import os
from src.listing_execution.services.application_service import ExecutionApplicationService
from src.listing_execution.models.execution_payload import ExecutionPayload

class ExecutionWorkflow:
    def __init__(self, application_service: ExecutionApplicationService):
        self.application_service = application_service
        
    def execute_listing_workflow(self, payload_dict: Dict[str, Any], dry_run: bool = True, credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Orchestrator workflow extension for live execution.
        """
        import uuid
        payload_kwargs = {
            "listing_id": payload_dict.get("listing_id"),
            "seller": payload_dict.get("seller"),
            "sku": payload_dict.get("sku", ""),
            "bundle_state": payload_dict.get("bundle_state", "none"),
            "market_eval": payload_dict.get("market_eval", {}),
            "profitability_score": payload_dict.get("profitability_score", 0.0),
            "environment": payload_dict.get("environment", "sandbox"),
            "dry_run": dry_run,
            "attempt_id": payload_dict.get("attempt_id") or f"att_{uuid.uuid4().hex[:8]}"
        }
            
        payload = ExecutionPayload(**payload_kwargs)
        
        candidate_data = payload_dict.get("candidate_data", {})
        seller_data = payload_dict.get("seller_data", {})
        handoff_data = payload_dict.get("handoff_data", {})
        
        if not dry_run and not credentials:
            # try from env
            token = os.environ.get("EBAY_AUTH_TOKEN")
            app_id = os.environ.get("EBAY_APP_ID")
            cert_id = os.environ.get("EBAY_CERT_ID")
            if token and app_id and cert_id:
                credentials = {
                    "auth_token": token,
                    "app_id": app_id,
                    "cert_id": cert_id
                }
            else:
                return {
                    "status": "failed",
                    "error_reason": "Missing credentials for live execution"
                }

        result = self.application_service.execute_with_live_gateway(
            payload=payload,
            credentials=credentials,
            candidate_data=candidate_data,
            seller_data=seller_data,
            handoff_data=handoff_data
        )
        
        return result
