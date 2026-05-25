import os
from flask import Flask, request, jsonify, Blueprint
from src.listing_execution.cli import get_service
from src.listing_execution.models.execution_payload import ExecutionPayload

execution_bp = Blueprint('execution', __name__, url_prefix='/execution')
_app_service_instance = get_service()

def _get_app_service():
    return _app_service_instance
    
def get_credentials_from_header(req):
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split("Bearer ")[1]
    return {
        "auth_token": token,
        "app_id": os.environ.get("EBAY_APP_ID", "dummy_app"),
        "cert_id": os.environ.get("EBAY_CERT_ID", "dummy_cert")
    }

@execution_bp.route('/execute/live', methods=['POST'])
def execute_live():
    service = _get_app_service()
    data = request.json or {}
    
    dry_run = data.get("dry_run", True)
    is_live = not dry_run
    
    credentials = None
    if is_live:
        credentials = data.get("credentials")
        if not credentials:
            credentials = get_credentials_from_header(request)
        if not credentials:
            return jsonify({"status": "failed", "error_reason": "Missing credentials for live execution"}), 400

    import uuid
    payload_kwargs = {
        "listing_id": data.get("listing_id"),
        "seller": data.get("seller"),
        "sku": data.get("sku", ""),
        "bundle_state": data.get("bundle_state", "none"),
        "market_eval": data.get("market_eval", {}),
        "profitability_score": data.get("profitability_score", 0.0),
        "environment": data.get("environment", "sandbox"),
        "dry_run": dry_run,
        "attempt_id": data.get("attempt_id") or f"att_{uuid.uuid4().hex[:8]}"
    }
        
    payload = ExecutionPayload(**payload_kwargs)
    
    candidate_data = data.get("candidate_data", {})
    seller_data = data.get("seller_data", {})
    handoff_data = data.get("handoff_data", {})
    
    result = service.execute_with_live_gateway(
        payload=payload,
        credentials=credentials,
        candidate_data=candidate_data,
        seller_data=seller_data,
        handoff_data=handoff_data
    )
    
    status_code = 200
    if result.get("status") == "rejected":
        status_code = 422
    elif result.get("status") == "failed":
        status_code = 400
        
    return jsonify(result), status_code

@execution_bp.route('/<attempt_id>/full', methods=['GET'])
def get_full_attempt(attempt_id):
    service = _get_app_service()
    result = service.get_attempt_status(attempt_id)
    if not result:
        return jsonify({"error": "not found"}), 404
        
    listing_id = result.get("listing_id", "")
    state = service.sync_service._get_current_state(listing_id)
    
    alert_level = "INFO"
    for log in reversed(service.monitor._audit_logs):
        if log.get("attempt_id") == attempt_id:
            alert_level = log.get("alert_level", "INFO")
            break
            
    return jsonify({
        "execution_result": result,
        "listing_state": state.value if hasattr(state, "value") else str(state),
        "alert_level": alert_level,
        "retry_info": {
            "retry_count": result.get("retry_count", 0)
        }
    }), 200

def create_app():
    app = Flask(__name__)
    app.register_blueprint(execution_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5000)
