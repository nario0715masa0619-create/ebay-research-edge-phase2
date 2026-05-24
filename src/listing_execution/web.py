from flask import Flask, request, jsonify
from src.listing_execution.cli import get_service
from src.listing_execution.models.execution_payload import ExecutionPayload

app = Flask(__name__)
_app_service_instance = get_service()

def _get_app_service():
    # In a real app, DB URL comes from config, and Session is injected.
    return _app_service_instance

@app.route('/execution/readiness', methods=['GET', 'POST'])
def check_readiness():
    service = _get_app_service()
    if request.method == 'POST':
        data = request.json
    else:
        data = request.args.to_dict()
        
    candidate_data = data.get("candidate_data", {})
    seller_data = data.get("seller_data", {})
    handoff_data = data.get("handoff_data", {})
    
    result = service.check_readiness(candidate_data, seller_data, handoff_data)
    return jsonify({
        "is_ready": result.is_ready,
        "score": result.readiness_score,
        "reasons": result.readiness_reasons
    })

@app.route('/execution/execute', methods=['POST'])
def execute_listing():
    service = _get_app_service()
    data = request.json
    
    candidate_data = data.get("candidate_data", {})
    seller_data = data.get("seller_data", {})
    handoff_data = data.get("handoff_data", {})

    payload = ExecutionPayload(
        attempt_id=data.get("attempt_id"),
        listing_id=data.get("listing_id"),
        seller=data.get("seller"),
        sku=data.get("sku", ""),
        bundle_state=data.get("bundle_state", "none"),
        market_eval=data.get("market_eval", {}),
        profitability_score=data.get("profitability_score", 0.0),
        environment=data.get("environment"),
        dry_run=data.get("dry_run", False)
    )
    
    result = service.execute_listing(payload, candidate_data, seller_data, handoff_data)
    status_code = 200 if result["status"] == "success" else 400
    if result["status"] == "rejected":
        status_code = 422
    
    return jsonify(result), status_code

@app.route('/execution/<attempt_id>', methods=['GET'])
def get_attempt(attempt_id):
    service = _get_app_service()
    result = service.get_attempt_status(attempt_id)
    if not result:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)

@app.route('/execution/<attempt_id>/retry', methods=['POST'])
def retry_execution(attempt_id):
    # Pass-through to retry logic
    return jsonify({"status": "retry_triggered", "attempt_id": attempt_id})

@app.route('/execution/<attempt_id>/rollback', methods=['POST'])
def rollback_execution(attempt_id):
    service = _get_app_service()
    reason = request.json.get("reason", "API Requested")
    result = service.rollback_execution(attempt_id, reason)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
