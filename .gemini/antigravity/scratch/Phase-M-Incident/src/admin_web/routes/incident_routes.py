from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
import uuid
from typing import Optional

# These dependencies would normally be injected or passed via app context
# For this implementation, we will assume they are set on the blueprint
incident_bp = Blueprint('incident_bp', __name__, url_prefix='/ops/incidents')

def get_dashboard_service():
    return incident_bp.dashboard_service

def get_management_service():
    return incident_bp.management_service

def get_detection_service():
    return incident_bp.detection_service

def get_repo():
    return incident_bp.repo

def get_event_repo():
    return incident_bp.event_repo

def get_link_repo():
    return incident_bp.link_repo

@incident_bp.route('/', methods=['GET'])
def list_incidents():
    status = request.args.get('status')
    severity = request.args.get('severity')
    seller = request.args.get('seller')
    environment = request.args.get('environment')
    overdue_only = request.args.get('overdue') == 'true'
    breached_only = request.args.get('breached') == 'true'

    repo = get_repo()
    incs = repo.get_all_incidents()
    filtered = []
    
    # Very basic SLA badge calculation matching CLI
    import datetime
    from src.incident.models.incident import SlaState
    now = datetime.datetime.utcnow()
    
    for inc in incs:
        if status and inc.incident_status.value != status: continue
        if severity and inc.severity.value != severity: continue
        if seller and inc.seller_account_id != seller: continue
        if environment and inc.environment != environment: continue
        
        is_breach = inc.sla_state in [SlaState.ACK_BREACHED, SlaState.RESOLVE_BREACHED, SlaState.BOTH_BREACHED]
        ack_overdue = not inc.acknowledged_at and inc.ack_due_at and now > inc.ack_due_at
        res_overdue = not inc.resolved_at and inc.resolve_due_at and now > inc.resolve_due_at
        is_overdue = ack_overdue or res_overdue
        
        if overdue_only and not is_overdue: continue
        if breached_only and not is_breach: continue
        
        inc.is_breach = is_breach
        inc.is_overdue = is_overdue
        
        filtered.append(inc)

    return render_template('incidents/list.html', incidents=filtered)

@incident_bp.route('/<incident_id>', methods=['GET'])
def detail(incident_id):
    if incident_id in ["dashboard", "overdue", "breached", "candidates"]:
        abort(404)
        
    try:
        uid = uuid.UUID(incident_id)
        inc = get_repo().get_incident(uid)
    except Exception:
        abort(404)
        
    events = [e for e in get_event_repo().events if e.incident_id == uid]
    events.sort(key=lambda x: x.created_at)
    
    links = []
    if get_link_repo():
        links = [l for l in get_link_repo().links if l.incident_id == uid]
        
    return render_template('incidents/detail.html', incident=inc, events=events, links=links)

@incident_bp.route('/dashboard', methods=['GET'])
def dashboard():
    summary = get_dashboard_service().get_incident_summary(time_range_hours=24)
    recent = get_dashboard_service().get_open_incidents(limit=10)
    return render_template('incidents/dashboard.html', summary=summary, recent=recent)

@incident_bp.route('/overdue', methods=['GET'])
def overdue():
    incs = get_dashboard_service().get_overdue_incidents()
    # attach overdue min calculation
    import datetime
    now = datetime.datetime.utcnow()
    for inc in incs:
        if not inc.acknowledged_at and inc.ack_due_at and now > inc.ack_due_at:
            inc.overdue_mins = int((now - inc.ack_due_at).total_seconds() / 60)
        elif not inc.resolved_at and inc.resolve_due_at and now > inc.resolve_due_at:
            inc.overdue_mins = int((now - inc.resolve_due_at).total_seconds() / 60)
        else:
            inc.overdue_mins = 0
            
    incs.sort(key=lambda x: x.overdue_mins, reverse=True)
    return render_template('incidents/overdue.html', incidents=incs)

@incident_bp.route('/breached', methods=['GET'])
def breached():
    incs = get_dashboard_service().get_breached_incidents()
    return render_template('incidents/breached.html', incidents=incs)

@incident_bp.route('/candidates', methods=['GET'])
def candidates():
    # Mock auto-detection execution for preview
    cands = get_detection_service().detect_from_alert_burst() # simple mock
    return render_template('incidents/candidates.html', candidates=cands)

@incident_bp.route('/<incident_id>/acknowledge', methods=['POST'])
def acknowledge(incident_id):
    try:
        get_management_service().acknowledge_incident(uuid.UUID(incident_id), "web_user", request.form.get("note", ""))
        return redirect(url_for('incident_bp.detail', incident_id=incident_id))
    except Exception as e:
        abort(400, description=str(e))

@incident_bp.route('/<incident_id>/assign', methods=['POST'])
def assign(incident_id):
    try:
        get_management_service().assign_incident(uuid.UUID(incident_id), request.form.get("owner", "unassigned"), "web_user")
        return redirect(url_for('incident_bp.detail', incident_id=incident_id))
    except Exception as e:
        abort(400, description=str(e))

@incident_bp.route('/<incident_id>/resolve', methods=['POST'])
def resolve(incident_id):
    try:
        get_management_service().resolve_incident(uuid.UUID(incident_id), "web_user", request.form.get("note", ""))
        return redirect(url_for('incident_bp.detail', incident_id=incident_id))
    except Exception as e:
        abort(400, description=str(e))

@incident_bp.route('/<incident_id>/close', methods=['POST'])
def close(incident_id):
    try:
        get_management_service().close_incident(uuid.UUID(incident_id), "web_user", request.form.get("note", ""))
        return redirect(url_for('incident_bp.detail', incident_id=incident_id))
    except Exception as e:
        abort(400, description=str(e))

@incident_bp.route('/<incident_id>/reopen', methods=['POST'])
def reopen(incident_id):
    try:
        get_management_service().reopen_incident(uuid.UUID(incident_id), "web_user", request.form.get("reason", ""))
        return redirect(url_for('incident_bp.detail', incident_id=incident_id))
    except Exception as e:
        abort(400, description=str(e))
