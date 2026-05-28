from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from uuid import UUID
from datetime import datetime

from src.learning.services.learning_record_service import LearningRecordService
from src.learning.services.root_cause_analysis_service import RootCauseAnalysisService
from src.learning.services.learning_recommendation_service import LearningRecommendationService
from src.learning.services.learning_candidate_service import LearningCandidateService
from src.learning.services.learning_dashboard_service import LearningDashboardService
from src.learning.services.recurring_issue_analysis_service import RecurringIssueAnalysisService
from src.learning.services.false_signal_analysis_service import FalseSignalAnalysisService

from src.learning.models.learning_record import LearningRecordStatus, RootCauseCategory
from src.learning.models.learning_recommendation import RecommendationStatus, RecommendationType

learning_bp = Blueprint('learning', __name__, url_prefix='/ops/learning')

# Global services for demo/in-memory purposes
learning_record_service = LearningRecordService()
root_cause_analysis_service = RootCauseAnalysisService()
learning_recommendation_service = LearningRecommendationService()
learning_candidate_service = LearningCandidateService()
learning_dashboard_service = LearningDashboardService()
recurring_issue_analysis_service = RecurringIssueAnalysisService()
false_signal_analysis_service = FalseSignalAnalysisService()

def _parse_uuid(s: str) -> UUID:
    try:
        return UUID(s)
    except ValueError:
        abort(400, "Invalid UUID format")

@learning_bp.route('/')
def list_records():
    status = request.args.get('status')
    category = request.args.get('category')
    seller = request.args.get('seller')
    env = request.args.get('environment')
    fp_only = request.args.get('false_positive') == 'true'
    limit = int(request.args.get('limit', 100))
    
    st = LearningRecordStatus(status) if status else None
    cat = RootCauseCategory(category) if category else None
    
    records, _ = learning_record_service.list_learning_records(
        status=st, category=cat, seller_account_id=seller, environment=env, limit=limit
    )
    if fp_only:
        records = [r for r in records if r.is_false_positive]
        
    return render_template('learning/list.html', records=records)

@learning_bp.route('/<learning_record_id>')
def detail(learning_record_id):
    if learning_record_id in ['dashboard', 'recommendations', 'recurring', 'candidates']:
        abort(404)
        
    lid = _parse_uuid(learning_record_id)
    rec = learning_record_service.get_learning_record_by_id(lid)
    if not rec:
        abort(404, "Learning record not found")
        
    rcas = root_cause_analysis_service.get_rcas_by_learning_record(lid)
    all_recs, _ = learning_recommendation_service.list_recommendations(limit=1000)
    recs = [r for r in all_recs if r.learning_record_id == lid]
    
    return render_template('learning/detail.html', record=rec, rcas=rcas, recommendations=recs)

@learning_bp.route('/dashboard')
def dashboard():
    summary = learning_dashboard_service.get_learning_summary()
    top_causes = learning_dashboard_service.get_top_root_causes()
    recurring = learning_dashboard_service.get_recurring_issue_summary()
    fp_stats = learning_dashboard_service.get_false_signal_summary()
    stale = learning_dashboard_service.get_stale_learning_backlog()
    pending_recs = learning_dashboard_service.get_recommendation_queue()
    
    return render_template('learning/dashboard.html', summary=summary, top_causes=top_causes, recurring=recurring, fp_stats=fp_stats, stale=stale, pending_recs=pending_recs)

@learning_bp.route('/recommendations')
def list_recommendations():
    status = request.args.get('status')
    phase = request.args.get('target_phase')
    priority_min = int(request.args.get('priority_min', 0))
    limit = int(request.args.get('limit', 50))
    
    st = RecommendationStatus(status) if status else None
    
    recs, _ = learning_recommendation_service.list_recommendations(
        status=st, target_phase=phase, priority_min=priority_min, limit=limit
    )
    return render_template('learning/recommendations.html', recommendations=recs)

@learning_bp.route('/recurring')
def recurring():
    limit = int(request.args.get('limit', 10))
    clusters = recurring_issue_analysis_service.identify_high_impact_clusters(limit)
    return render_template('learning/recurring.html', clusters=clusters)

@learning_bp.route('/candidates')
def candidates():
    limit = int(request.args.get('limit', 50))
    cands = learning_candidate_service.scan_all_candidates(limit)
    return render_template('learning/candidates.html', candidates=cands)

@learning_bp.route('/<learning_record_id>/add-rca', methods=['POST'])
def add_rca(learning_record_id):
    lid = _parse_uuid(learning_record_id)
    if not learning_record_service.get_learning_record_by_id(lid):
        abort(404)
        
    problem = request.form.get('problem', '')
    cause = request.form.get('cause', '')
    resolution = request.form.get('resolution', '')
    prevention = request.form.get('prevention', '')
    
    root_cause_analysis_service.create_rca(
        lid, problem, "symptoms", cause, "factors", "mitigation", resolution, prevention, "web_user"
    )
    flash("RCA added successfully", "success")
    return redirect(url_for('learning.detail', learning_record_id=str(lid)))

@learning_bp.route('/<learning_record_id>/add-recommendation', methods=['POST'])
def add_recommendation(learning_record_id):
    lid = _parse_uuid(learning_record_id)
    if not learning_record_service.get_learning_record_by_id(lid):
        abort(404)
        
    rtype = request.form.get('type')
    phase = request.form.get('target_phase')
    proposal = request.form.get('proposal_summary', '')
    priority = int(request.form.get('priority', 50))
    
    try:
        enum_rtype = RecommendationType(rtype)
    except ValueError:
        abort(400, "Invalid type")
        
    learning_recommendation_service.create_recommendation(
        lid, enum_rtype, phase, "scope", proposal, "details", priority, datetime.utcnow(), "web_user"
    )
    flash("Recommendation added successfully", "success")
    return redirect(url_for('learning.detail', learning_record_id=str(lid)))

@learning_bp.route('/<learning_record_id>/close', methods=['POST'])
def close_record(learning_record_id):
    lid = _parse_uuid(learning_record_id)
    try:
        learning_record_service.close_learning_record(lid)
        flash("Record closed", "success")
    except ValueError:
        abort(404)
    return redirect(url_for('learning.detail', learning_record_id=str(lid)))

@learning_bp.route('/recommendation/<recommendation_id>/approve', methods=['POST'])
def approve_recommendation(recommendation_id):
    rid = _parse_uuid(recommendation_id)
    try:
        learning_recommendation_service.approve_recommendation(rid, "web_user")
        flash("Recommendation approved", "success")
    except ValueError:
        abort(404)
    return redirect(url_for('learning.list_recommendations'))

@learning_bp.route('/recommendation/<recommendation_id>/reject', methods=['POST'])
def reject_recommendation(recommendation_id):
    rid = _parse_uuid(recommendation_id)
    reason = request.form.get('reason', 'Rejected via web')
    try:
        learning_recommendation_service.reject_recommendation(rid, reason)
        flash("Recommendation rejected", "success")
    except ValueError:
        abort(404)
    return redirect(url_for('learning.list_recommendations'))
