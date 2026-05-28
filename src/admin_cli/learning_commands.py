import sys
import json
import csv
from uuid import UUID
from datetime import datetime

from src.learning.services.learning_record_service import LearningRecordService
from src.learning.services.root_cause_analysis_service import RootCauseAnalysisService
from src.learning.services.learning_recommendation_service import LearningRecommendationService
from src.learning.services.learning_candidate_service import LearningCandidateService
from src.learning.services.learning_dashboard_service import LearningDashboardService
from src.learning.services.recurring_issue_analysis_service import RecurringIssueAnalysisService
from src.learning.services.false_signal_analysis_service import FalseSignalAnalysisService

from src.learning.models.learning_record import LearningRecordStatus, RootCauseCategory, ImpactScope
from src.learning.models.learning_recommendation import RecommendationStatus, RecommendationType

# Global service instances for CLI memory
learning_record_service = LearningRecordService()
root_cause_analysis_service = RootCauseAnalysisService()
learning_recommendation_service = LearningRecommendationService()
learning_candidate_service = LearningCandidateService()
learning_dashboard_service = LearningDashboardService()
recurring_issue_analysis_service = RecurringIssueAnalysisService()
false_signal_analysis_service = FalseSignalAnalysisService()

def _output(data: list, format_type: str, headers: list, output_file: str = None):
    out = ""
    if format_type == "json":
        out = json.dumps(data, indent=2, default=str)
    elif format_type == "csv":
        import io
        s = io.StringIO()
        writer = csv.DictWriter(s, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        out = s.getvalue()
    else:
        # Table
        if not data:
            out = "No data"
        else:
            out = " | ".join(headers) + "\n"
            for row in data:
                out += " | ".join(str(row.get(h, "")) for h in headers) + "\n"
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        print(out)

def parse_uuid(s: str) -> UUID:
    try:
        return UUID(s)
    except ValueError:
        print("Invalid UUID format")
        sys.exit(2)

def candidate_scan(args):
    limit = getattr(args, "limit", 50)
    candidates = learning_candidate_service.scan_all_candidates(limit)
    data = []
    for c in candidates:
        data.append({
            "ID": str(c.candidate_id),
            "SOURCE": c.candidate_source.value,
            "CATEGORY": c.suggested_root_cause_category.value,
            "SCORE": c.confidence_score
        })
    _output(data, args.format, ["ID", "SOURCE", "CATEGORY", "SCORE"], args.output_file)

def list_records(args):
    status = LearningRecordStatus(args.status) if getattr(args, "status", None) else None
    category = RootCauseCategory(args.category) if getattr(args, "category", None) else None
    seller = getattr(args, "seller", None)
    env = getattr(args, "env", None)
    limit = getattr(args, "limit", 100)
    
    recs, _ = learning_record_service.list_learning_records(status=status, category=category, seller_account_id=seller, environment=env, limit=limit)
    if getattr(args, "false_positive_only", False):
        recs = [r for r in recs if r.is_false_positive]
        
    data = []
    for r in recs:
        data.append({
            "LEARNING_ID": str(r.learning_record_id),
            "STATUS": r.status.value,
            "CATEGORY": r.root_cause_category.value,
            "SELLER": r.seller_account_id or "N/A",
            "ENV": r.environment or "N/A",
            "EFFECTIVENESS": r.effectiveness_rating.value,
            "CREATED_AT": r.created_at.isoformat()
        })
    _output(data, args.format, ["LEARNING_ID", "STATUS", "CATEGORY", "SELLER", "ENV", "EFFECTIVENESS", "CREATED_AT"], args.output_file)

def show_record(args):
    lid = parse_uuid(args.learning_id)
    rec = learning_record_service.get_learning_record_by_id(lid)
    if not rec:
        print("Learning record not found")
        sys.exit(1)
        
    rcas = root_cause_analysis_service.get_rcas_by_learning_record(lid)
    recs_all, _ = learning_recommendation_service.list_recommendations(limit=1000)
    recs = [r for r in recs_all if r.learning_record_id == lid]
    
    if args.format == "json":
        data = {
            "learning_record": rec.__dict__,
            "rcas": [r.__dict__ for r in rcas],
            "recommendations": [r.__dict__ for r in recs]
        }
        _output([data], args.format, ["data"], args.output_file)
        return
        
    out = f"=== LEARNING RECORD DETAIL ===\nID: {rec.learning_record_id}\nTitle: {rec.title}\nStatus: {rec.status.value}\nCategory: {rec.root_cause_category.value}\n"
    out += f"\n=== RCAs ({len(rcas)}) ===\n"
    for rca in rcas:
        out += f"- RCA {rca.rca_id}: {rca.problem_statement}\n"
    out += f"\n=== RECOMMENDATIONS ({len(recs)}) ===\n"
    for r in recs:
        out += f"- Rec {r.recommendation_id}: [{r.recommendation_status.value}] {r.recommendation_type.value}\n"
        
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        print(out)

def create_from_incident(args):
    iid = parse_uuid(args.incident_id)
    try:
        cat = RootCauseCategory(args.category)
    except ValueError:
        print("Invalid category")
        sys.exit(2)
        
    title = getattr(args, "title", f"Learning from incident {iid}")
    if args.dry_run:
        print("DRY RUN: create_from_incident")
        return
        
    rec = learning_record_service.create_learning_record(title, "Generated from CLI", cat, ImpactScope.GLOBAL, "cli_user", linked_incident_id=iid)
    print(f"Created Learning Record: {rec.learning_record_id}")

def add_rca(args):
    lid = parse_uuid(args.learning_id)
    if not learning_record_service.get_learning_record_by_id(lid):
        print("Learning record not found")
        sys.exit(1)
        
    if args.dry_run:
        print("DRY RUN: add_rca")
        return
        
    rca = root_cause_analysis_service.create_rca(
        lid, args.problem, "symptoms", args.cause, "factors", "mitigation", args.resolution, getattr(args, "prevention", ""), "cli_user"
    )
    print(f"Created RCA: {rca.rca_id}")

def add_recommendation(args):
    lid = parse_uuid(args.learning_id)
    if not learning_record_service.get_learning_record_by_id(lid):
        print("Learning record not found")
        sys.exit(1)
        
    try:
        rtype = RecommendationType(args.type)
    except ValueError:
        print("Invalid type")
        sys.exit(2)
        
    if args.dry_run:
        print("DRY RUN: add_recommendation")
        return
        
    rec = learning_recommendation_service.create_recommendation(
        lid, rtype, args.target_phase, "scope", args.proposal, "details", int(args.priority), datetime.utcnow(), "cli_user"
    )
    print(f"Created Recommendation: {rec.recommendation_id}")

def close_record(args):
    lid = parse_uuid(args.learning_id)
    if args.dry_run:
        print("DRY RUN: close_record")
        return
        
    try:
        rec = learning_record_service.close_learning_record(lid)
        print(f"Closed Learning Record: {rec.learning_record_id}")
    except ValueError as e:
        print(f"Learning record not found: {e}")
        sys.exit(1)

def learning_digest(args):
    out = "# Learning Digest\n\nGenerated digest."
    if args.format == "json":
        _output([{"digest": out}], "json", ["digest"], args.output_file)
        return
        
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        print(out)

def recurring_issues(args):
    limit = getattr(args, "limit", 10)
    clusters = recurring_issue_analysis_service.identify_high_impact_clusters(limit)
    data = []
    for c in clusters:
        data.append({
            "CLUSTER_ID": c.get("cluster_id", "N/A"),
            "CAUSE": str(c.get("root_cause_category", "N/A")),
            "SELLERS": str(c.get("affected_sellers", "N/A")),
            "ENVS": str(c.get("affected_environments", "N/A")),
            "OCCURRENCE": str(c.get("occurrence_count", "N/A")),
            "RECENT_AT": str(c.get("most_recent_at", "N/A"))
        })
    _output(data, args.format, ["CLUSTER_ID", "CAUSE", "SELLERS", "ENVS", "OCCURRENCE", "RECENT_AT"], args.output_file)

def false_signals(args):
    fps = false_signal_analysis_service.identify_false_positives()
    data = []
    for f in fps:
        data.append({
            "ID": f.get("incident_id", "N/A"),
            "TYPE": "fp",
            "PATTERN": f.get("reason", "N/A"),
            "COUNT": 1,
            "LAST_OCCURRENCE": "N/A"
        })
    _output(data, args.format, ["ID", "TYPE", "PATTERN", "COUNT", "LAST_OCCURRENCE"], args.output_file)

def list_recommendations(args):
    status = RecommendationStatus(args.status) if getattr(args, "status", None) else None
    phase = getattr(args, "target_phase", None)
    priority_min = int(getattr(args, "priority_min", 0))
    limit = int(getattr(args, "limit", 20))
    
    recs, _ = learning_recommendation_service.list_recommendations(status=status, target_phase=phase, priority_min=priority_min, limit=limit)
    data = []
    for r in recs:
        data.append({
            "REC_ID": str(r.recommendation_id),
            "TYPE": r.recommendation_type.value,
            "TARGET_PHASE": r.target_phase,
            "PRIORITY": r.priority,
            "STATUS": r.recommendation_status.value,
            "REVIEW_DUE": r.review_due_at.isoformat()
        })
    _output(data, args.format, ["REC_ID", "TYPE", "TARGET_PHASE", "PRIORITY", "STATUS", "REVIEW_DUE"], args.output_file)

def approve_recommendation(args):
    rid = parse_uuid(args.recommendation_id)
    if not learning_recommendation_service.get_recommendation_by_id(rid):
        print("Recommendation not found")
        sys.exit(1)
        
    if args.dry_run:
        print("DRY RUN: approve_recommendation")
        return
        
    rec = learning_recommendation_service.approve_recommendation(rid, "cli_user")
    print(f"Approved Recommendation: {rec.recommendation_id}")

def reject_recommendation(args):
    rid = parse_uuid(args.recommendation_id)
    if not learning_recommendation_service.get_recommendation_by_id(rid):
        print("Recommendation not found")
        sys.exit(1)
        
    if args.dry_run:
        print("DRY RUN: reject_recommendation")
        return
        
    rec = learning_recommendation_service.reject_recommendation(rid, args.reason)
    print(f"Rejected Recommendation: {rec.recommendation_id}")

def learning_dashboard(args):
    summary = learning_dashboard_service.get_learning_summary()
    if args.format == "json":
        _output([summary], "json", ["summary"], args.output_file)
        return
        
    out = "=== LEARNING DASHBOARD ===\n"
    out += f"Total Records: {summary['total_records']}\n"
    out += f"False Positives: {summary['false_positive_count']}\n"
    out += f"Recurring Clusters: {summary['recurring_clusters']}\n"
    
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        print(out)
