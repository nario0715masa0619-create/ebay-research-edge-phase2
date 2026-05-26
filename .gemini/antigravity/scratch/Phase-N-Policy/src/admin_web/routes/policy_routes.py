from flask import Blueprint, request, render_template, redirect, url_for, abort, flash, current_app
from uuid import UUID
from datetime import datetime

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, Severity
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.services.ops_policy_dashboard_service import OpsPolicyDashboardService
from src.ops_policy.services.ops_policy_digest_service import OpsPolicyDigestService
from src.ops_policy.services.incident_detection_service import IncidentDetectionService
from src.ops_policy.services.ops_policy_state_machine import OpsPolicyStateMachine, InvalidStateTransitionError

policy_bp = Blueprint('policy', __name__, url_prefix='/ops/policies')

# Typically injected, using instances here for simplicity
management_service = OpsPolicyManagementService()
dashboard_service = OpsPolicyDashboardService(management_service)
digest_service = OpsPolicyDigestService(management_service)
detection_service = IncidentDetectionService()
state_machine = OpsPolicyStateMachine()

@policy_bp.route('/', methods=['GET'])
def list_policies():
    status_str = request.args.get('status')
    scope_str = request.args.get('scope')
    seller = request.args.get('seller')
    env = request.args.get('environment')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    try:
        status = PolicyStatus(status_str.lower()) if status_str else None
        scope = ScopeType(scope_str.lower()) if scope_str else None
    except ValueError:
        abort(400, "Invalid status or scope")

    policies, total = management_service.list_policies(
        scope_type=scope,
        status=status,
        seller_account_id=seller,
        environment=env,
        limit=limit,
        offset=offset
    )

    return render_template('policies/list.html', policies=policies, total=total, PolicyStatus=PolicyStatus, ScopeType=ScopeType, ActionType=ActionType)

@policy_bp.route('/<policy_id>', methods=['GET'])
def policy_detail(policy_id):
    try:
        pid = UUID(policy_id)
    except ValueError:
        abort(400, "Invalid UUID")

    policy = management_service.get_policy_by_id(pid)
    if not policy:
        abort(404, "Policy not found")

    events = management_service.list_policy_events(pid)
    
    return render_template('policies/detail.html', policy=policy, events=events, PolicyStatus=PolicyStatus)

@policy_bp.route('/dashboard', methods=['GET'])
def dashboard():
    summary = dashboard_service.get_policy_summary()
    top_sellers = dashboard_service.get_top_affected_sellers()
    return render_template('policies/dashboard.html', summary=summary, top_sellers=top_sellers)

@policy_bp.route('/candidates', methods=['GET'])
def candidates():
    severity_str = request.args.get('severity')
    limit = int(request.args.get('limit', 20))

    all_cands = detection_service.scan_all_candidates()
    
    if severity_str:
        try:
            sev = Severity(severity_str.lower())
            all_cands = [c for c in all_cands if c.severity == sev]
        except ValueError:
            abort(400, "Invalid severity")
            
    cands = all_cands[:limit]
    
    return render_template('policies/candidates.html', candidates=cands)

@policy_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template('policies/create.html', ScopeType=ScopeType, ActionType=ActionType)
        
    action_str = request.form.get('action')
    scope_str = request.form.get('scope')
    target = request.form.get('target') or None
    title = request.form.get('title')
    reason = request.form.get('reason')
    
    if not all([action_str, scope_str, title, reason]):
        abort(400, "Missing required fields")
        
    try:
        action = ActionType(action_str.lower())
        scope = ScopeType(scope_str.lower())
    except ValueError:
        abort(400, "Invalid action or scope")
        
    policy = management_service.create_manual_policy(
        scope_type=scope,
        target_id=target,
        action_type=action,
        title=title,
        reason=reason,
        created_by="web_user"
    )
    
    flash("Policy created successfully", "success")
    return redirect(url_for('policy.policy_detail', policy_id=str(policy.policy_id)))

def _do_transition(policy_id_str, target_status, reason, review_due_str=None):
    try:
        pid = UUID(policy_id_str)
    except ValueError:
        abort(400, "Invalid UUID")

    policy = management_service.get_policy_by_id(pid)
    if not policy:
        abort(404, "Policy not found")
        
    if not state_machine.validate_transition(policy.status, target_status):
        abort(409, f"Invalid state transition from {policy.status.name} to {target_status.name}")
        
    policy.status = target_status
    if target_status == PolicyStatus.APPROVED:
        policy.approved_by = "web_user"
        if review_due_str:
            policy.review_due_at = datetime.fromisoformat(review_due_str)
    elif target_status == PolicyStatus.ACTIVE:
        policy.applied_at = datetime.utcnow()
    elif target_status == PolicyStatus.RELEASED:
        policy.released_at = datetime.utcnow()
    elif target_status == PolicyStatus.EXPIRED:
        policy.is_expired = True

    management_service.add_policy_note(pid, reason or f"Transitioned to {target_status.name}", "web_user")
    return policy

@policy_bp.route('/<policy_id>/approve', methods=['POST'])
def approve(policy_id):
    review_due_str = request.form.get('review_due')
    policy = management_service.get_policy_by_id(UUID(policy_id))
    if policy and policy.level.name == "STRONG" and not review_due_str and not policy.review_due_at:
        abort(400, "review_due is required for strong policy")
        
    _do_transition(policy_id, PolicyStatus.APPROVED, "Approved via Web", review_due_str)
    flash("Policy approved", "success")
    return redirect(url_for('policy.policy_detail', policy_id=policy_id))

@policy_bp.route('/<policy_id>/activate', methods=['POST'])
def activate(policy_id):
    _do_transition(policy_id, PolicyStatus.ACTIVE, "Activated via Web")
    flash("Policy activated", "success")
    return redirect(url_for('policy.policy_detail', policy_id=policy_id))

@policy_bp.route('/<policy_id>/release', methods=['POST'])
def release(policy_id):
    _do_transition(policy_id, PolicyStatus.RELEASED, "Released via Web")
    flash("Policy released", "success")
    return redirect(url_for('policy.policy_detail', policy_id=policy_id))

@policy_bp.route('/<policy_id>/reject', methods=['POST'])
def reject(policy_id):
    reason = request.form.get('reason', "Rejected via Web")
    _do_transition(policy_id, PolicyStatus.REJECTED, reason)
    flash("Policy rejected", "success")
    return redirect(url_for('policy.policy_detail', policy_id=policy_id))

@policy_bp.route('/<policy_id>/cancel', methods=['POST'])
def cancel(policy_id):
    reason = request.form.get('reason', "Cancelled via Web")
    _do_transition(policy_id, PolicyStatus.CANCELLED, reason)
    flash("Policy cancelled", "success")
    return redirect(url_for('policy.policy_detail', policy_id=policy_id))

@policy_bp.route('/<policy_id>/digest', methods=['GET'])
def digest(policy_id):
    try:
        pid = UUID(policy_id)
    except ValueError:
        abort(400, "Invalid UUID")
        
    policy = management_service.get_policy_by_id(pid)
    if not policy:
        abort(404, "Policy not found")
        
    # Just render the individual policy details as markdown for simplicity
    markdown_content = f"# Policy {policy.title}\nID: {policy.policy_id}\n\nScope: {policy.scope_type.value}\nAction: {policy.action_type.value}\n"
    
    return render_template('policies/digest.html', policy=policy, markdown_content=markdown_content)
