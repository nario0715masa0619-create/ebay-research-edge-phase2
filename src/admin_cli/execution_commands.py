import os
import json
import argparse
from typing import Dict, Any, Optional

from src.listing_execution.services.application_service import ExecutionApplicationService
from src.listing_execution.cli import get_service
from src.listing_execution.models.execution_payload import ExecutionPayload

def get_credentials(args) -> Optional[Dict[str, str]]:
    if not args.live:
        return None
        
    if getattr(args, "credentials_file", None):
        with open(args.credentials_file, 'r') as f:
            return json.load(f)
            
    token = os.environ.get("EBAY_AUTH_TOKEN")
    app_id = os.environ.get("EBAY_APP_ID")
    cert_id = os.environ.get("EBAY_CERT_ID")
    
    if not token or not app_id or not cert_id:
        raise ValueError("Live execution requires credentials. Set EBAY_AUTH_TOKEN, EBAY_APP_ID, EBAY_CERT_ID or use --credentials-file")
        
    return {
        "auth_token": token,
        "app_id": app_id,
        "cert_id": cert_id
    }

def execute_listing(args):
    service = get_service()
    
    payload_data = {}
    if getattr(args, "payload", None) and args.payload != "{}":
        try:
            payload_data = json.loads(args.payload)
        except json.JSONDecodeError:
            print(json.dumps({"status": "error", "error_reason": "Invalid JSON in payload"}))
            return
            
    candidate_data = payload_data.get("candidate_data", {})
    seller_data = payload_data.get("seller_data", {})
    handoff_data = payload_data.get("handoff_data", {})
    
    seller = args.seller if getattr(args, "seller", None) else payload_data.get("seller")
    listing_id = args.listing_id if getattr(args, "listing_id", None) else payload_data.get("listing_id")
    
    import uuid
    payload_kwargs = {
        "listing_id": listing_id,
        "seller": seller,
        "sku": payload_data.get("sku", ""),
        "bundle_state": payload_data.get("bundle_state", "none"),
        "market_eval": payload_data.get("market_eval", {}),
        "profitability_score": payload_data.get("profitability_score", 0.0),
        "environment": payload_data.get("environment", "sandbox"),
        "dry_run": not args.live,
        "attempt_id": payload_data.get("attempt_id") or f"att_{uuid.uuid4().hex[:8]}"
    }
        
    payload = ExecutionPayload(**payload_kwargs)
    
    try:
        credentials = get_credentials(args)
    except ValueError as e:
        print(json.dumps({"status": "failed", "error_reason": str(e)}))
        return

    result = service.execute_with_live_gateway(
        payload=payload,
        credentials=credentials,
        candidate_data=candidate_data,
        seller_data=seller_data,
        handoff_data=handoff_data
    )
    
    print(json.dumps(result, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Admin CLI Execution Commands")
    subparsers = parser.add_subparsers(dest="command")

    parser_execute = subparsers.add_parser("execute")
    parser_execute.add_argument("--seller")
    parser_execute.add_argument("--listing-id")
    parser_execute.add_argument("--payload", default="{}", help="JSON string of additional Payload Data")
    parser_execute.add_argument("--dry-run", action="store_true", default=True, help="Run in mock mode (default)")
    parser_execute.add_argument("--live", action="store_true", help="Run with Live API")
    parser_execute.add_argument("--credentials-file", help="Path to JSON file with credentials")
    
    args = parser.parse_args()
    
    if args.command == "execute":
        execute_listing(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
