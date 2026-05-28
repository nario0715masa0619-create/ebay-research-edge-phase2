import argparse
import sys
import json
from uuid import UUID
from datetime import datetime
import dataclasses

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel, Severity
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.services.ops_policy_dashboard_service import OpsPolicyDashboardService
from src.ops_policy.services.ops_policy_digest_service import OpsPolicyDigestService
from src.ops_policy.services.incident_detection_service import IncidentDetectionService
from src.ops_policy.services.ops_policy_state_machine import OpsPolicyStateMachine, InvalidStateTransitionError

# Dummy global instance for CLI (In reality, injected via DI)
management_service = OpsPolicyManagementService()
dashboard_service = OpsPolicyDashboardService(management_service)
digest_service = OpsPolicyDigestService(management_service)
detection_service = IncidentDetectionService()
state_machine = OpsPolicyStateMachine()

def handle_output(data, format_type, output_file=None):
    if format_type == "json":
        out_str = json.dumps(data, indent=2, default=str)
    elif format_type == "csv":
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                keys = data[0].keys()
                out_str = ",".join(keys) + "\n"
                for row in data:
                    out_str += ",".join(str(row.get(k, "")) for k in keys) + "\n"
            else:
                out_str = "data\n" + "\n".join(str(row) for row in data)
        else:
            out_str = "No data"
    else: # table/text
        if isinstance(data, list):
            if data:
                if isinstance(data[0], dict):
                    keys = data[0].keys()
                    out_str = " | ".join(keys) + "\n"
                    for row in data:
                        out_str += " | ".join(str(row.get(k, "")) for k in keys) + "\n"
                else:
                    out_str = "\n".join(str(row) for row in data)
            else:
                out_str = "No data"
        elif isinstance(data, dict):
            out_str = "\n".join(f"{k}: {v}" for k, v in data.items())
        else:
            out_str = str(data)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(out_str)
    else:
        print(out_str)

def scan(args):
    candidates = detection_service.scan_all_candidates()
    data = []
    for c in candidates:
        data.append({
            "ID": str(c.candidate_id),
            "SEVERITY": c.severity.name if c.severity else "",
            "ACTION": c.recommended_action_type.name if c.recommended_action_type else "",
            "SCOPE": c.target_scope.name if c.target_scope else "",
            "TARGET": c.target_id or "",
            "CREATED_AT": c.created_at.isoformat()
        })
    handle_output(data, args.format, args.output_file)

def candidate_list(args):
    candidates = detection_service.scan_all_candidates()
    if args.severity:
        sev = Severity(args.severity.lower())
        candidates = [c for c in candidates if c.severity == sev]
    candidates = candidates[:args.limit]
    data = []
    for c in candidates:
        data.append({
            "ID": str(c.candidate_id),
            "SEVERITY": c.severity.name if c.severity else "",
            "ACTION": c.recommended_action_type.name if c.recommended_action_type else "",
            "SCOPE": c.target_scope.name if c.target_scope else "",
            "TARGET": c.target_id or "",
            "CREATED_AT": c.created_at.isoformat()
        })
    handle_output(data, args.format, args.output_file)

def policy_list(args):
    status = PolicyStatus(args.status.lower()) if args.status else None
    scope = ScopeType(args.scope.lower()) if args.scope else None
    policies, _ = management_service.list_policies(
        scope_type=scope,
        status=status,
        seller_account_id=args.seller,
        environment=args.env,
        limit=args.limit
    )
    
    data = []
    for p in policies:
        data.append({
            "POLICY_ID": str(p.policy_id),
            "ACTION_TYPE": p.action_type.value,
            "SCOPE_TYPE": p.scope_type.value,
            "TARGET": p.target_id or "",
            "STATUS": p.status.value,
            "EFFECTIVE_FROM": p.effective_from.isoformat() if p.effective_from else "",
            "REVIEW_DUE": p.review_due_at.isoformat() if p.review_due_at else ""
        })
    handle_output(data, args.format, args.output_file)

def show(args):
    try:
        pid = UUID(args.policy_id)
    except ValueError:
        print("Invalid UUID")
        sys.exit(2)
        
    policy = management_service.get_policy_by_id(pid)
    if not policy:
        print("Policy not found")
        sys.exit(1)
        
    events = management_service.list_policy_events(pid)
    
    if args.format == "json":
        data = {
            "policy": dataclasses.asdict(policy),
            "events": [dataclasses.asdict(e) for e in events]
        }
    else:
        p_dict = dataclasses.asdict(policy)
        data = "=== POLICY DETAIL ===\n"
        data += "\n".join(f"{k}: {v}" for k, v in p_dict.items())
        data += "\n\n=== EVENTS ===\n"
        for e in events:
            data += f"[{e.created_at}] {e.event_type.value} by {e.actor_id}: {e.note}\n"
            
    handle_output(data, args.format, args.output_file)

def propose(args):
    action = ActionType(args.action.lower())
    scope = ScopeType(args.scope.lower())
    
    if args.dry_run:
        print("Dry-run: Policy would be created")
        return
        
    policy = management_service.create_manual_policy(
        scope_type=scope,
        target_id=args.target,
        action_type=action,
        title=args.title,
        reason=args.reason,
        created_by="cli_user"
    )
    data = {"policy_id": str(policy.policy_id), "status": "proposed"}
    handle_output(data, args.format, args.output_file)

def _transition_status(policy_id_str, target_status, reason, review_due_str=None, dry_run=False):
    try:
        pid = UUID(policy_id_str)
    except ValueError:
        print("Invalid UUID")
        sys.exit(2)
        
    policy = management_service.get_policy_by_id(pid)
    if not policy:
        print("Policy not found")
        sys.exit(1)

    # Approve requires review_due for STRONG
    if target_status == PolicyStatus.APPROVED and policy.level == PolicyLevel.STRONG:
        if not review_due_str and not policy.review_due_at:
            print("review-due required for strong")
            sys.exit(1)
            
    if dry_run:
        print(f"Dry-run: Policy {pid} would transition to {target_status.name}")
        return policy
        
    if not state_machine.validate_transition(policy.status, target_status):
        print(f"Invalid transition from {policy.status.name} to {target_status.name}")
        sys.exit(1)
        
    policy.status = target_status
    if target_status == PolicyStatus.APPROVED:
        policy.approved_by = "cli_user"
        if review_due_str:
            policy.review_due_at = datetime.fromisoformat(review_due_str)
    elif target_status == PolicyStatus.ACTIVE:
        policy.applied_at = datetime.utcnow()
    elif target_status == PolicyStatus.RELEASED:
        policy.released_at = datetime.utcnow()
    elif target_status == PolicyStatus.EXPIRED:
        policy.is_expired = True

    management_service.add_policy_note(pid, reason or f"Transitioned to {target_status.name}", "cli_user")
    return policy

def approve(args):
    p = _transition_status(args.policy_id, PolicyStatus.APPROVED, "Approved via CLI", args.review_due, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def activate(args):
    p = _transition_status(args.policy_id, PolicyStatus.ACTIVE, "Activated via CLI", None, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def reject(args):
    p = _transition_status(args.policy_id, PolicyStatus.REJECTED, args.reason, None, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def release(args):
    p = _transition_status(args.policy_id, PolicyStatus.RELEASED, "Released via CLI", None, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def expire(args):
    p = _transition_status(args.policy_id, PolicyStatus.EXPIRED, "Expired via CLI", None, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def cancel(args):
    p = _transition_status(args.policy_id, PolicyStatus.CANCELLED, args.reason, None, args.dry_run)
    handle_output({"policy_id": str(p.policy_id), "status": p.status.value}, args.format, args.output_file)

def dashboard(args):
    if args.seller:
        policies = dashboard_service.get_seller_policies(args.seller)
        summary = {"total_count": len(policies)}
    elif args.env:
        policies = dashboard_service.get_environment_policies(args.env)
        summary = {"total_count": len(policies)}
    else:
        summary = dashboard_service.get_policy_summary()
        # Convert enums in keys to strings for JSON
        if "by_scope_type" in summary:
            summary["by_scope_type"] = {k.value: v for k, v in summary["by_scope_type"].items()}
        if "by_action_type" in summary:
            summary["by_action_type"] = {k.value: v for k, v in summary["by_action_type"].items()}
            
    if args.format == "table":
        # Make a nicely formatted summary string
        out = "=== POLICY DASHBOARD ===\n"
        out += f"Total: {summary.get('total_count', 0)}\n"
        if "active_count" in summary:
            out += f"Active: {summary['active_count']}\n"
            out += f"Proposed: {summary['proposed_count']}\n"
            out += "\nBy Action:\n"
            for k, v in summary["by_action_type"].items():
                out += f"  {k}: {v}\n"
            out += "\nBy Scope:\n"
            for k, v in summary["by_scope_type"].items():
                out += f"  {k}: {v}\n"
        handle_output(out, args.format, args.output_file)
    else:
        handle_output(summary, args.format, args.output_file)

def digest(args):
    out = ""
    if args.type == "active":
        out = digest_service.generate_active_policy_digest()
    elif args.type == "seller":
        if not args.seller:
            print("Missing --seller")
            sys.exit(2)
        out = digest_service.generate_seller_policy_digest(args.seller)
    elif args.type == "environment":
        if not args.env:
            print("Missing --env")
            sys.exit(2)
        out = digest_service.generate_environment_policy_digest(args.env)
    elif args.type == "daily":
        d = datetime.fromisoformat(args.date) if args.date else datetime.utcnow()
        out = digest_service.generate_daily_policy_summary_digest(d)
    else:
        print("Invalid digest type")
        sys.exit(2)
        
    # Ignore format for digest, it's always markdown
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        print(out)


def main():
    parser = argparse.ArgumentParser(description="Ops Policy CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Common args
    for p in []:
        p.add_argument("--format", choices=["table", "json", "csv"], default="table")
        p.add_argument("--output-file")
        p.add_argument("--dry-run", action="store_true")

    def add_common_args(subp):
        subp.add_argument("--format", choices=["table", "json", "csv"], default="table")
        subp.add_argument("--output-file")
        subp.add_argument("--dry-run", action="store_true")

    p_scan = subparsers.add_parser("scan")
    p_scan.add_argument("--seller")
    p_scan.add_argument("--environment")
    add_common_args(p_scan)

    p_cand = subparsers.add_parser("candidate-list")
    p_cand.add_argument("--limit", type=int, default=20)
    p_cand.add_argument("--severity")
    add_common_args(p_cand)

    p_list = subparsers.add_parser("list")
    p_list.add_argument("--status")
    p_list.add_argument("--scope")
    p_list.add_argument("--seller")
    p_list.add_argument("--env")
    p_list.add_argument("--limit", type=int, default=100)
    add_common_args(p_list)

    p_show = subparsers.add_parser("show")
    p_show.add_argument("--policy-id", required=True)
    add_common_args(p_show)

    p_propose = subparsers.add_parser("propose")
    p_propose.add_argument("--action", required=True)
    p_propose.add_argument("--scope", required=True)
    p_propose.add_argument("--target")
    p_propose.add_argument("--title", required=True)
    p_propose.add_argument("--reason", required=True)
    add_common_args(p_propose)

    p_approve = subparsers.add_parser("approve")
    p_approve.add_argument("--policy-id", required=True)
    p_approve.add_argument("--review-due")
    add_common_args(p_approve)

    p_activate = subparsers.add_parser("activate")
    p_activate.add_argument("--policy-id", required=True)
    add_common_args(p_activate)

    p_reject = subparsers.add_parser("reject")
    p_reject.add_argument("--policy-id", required=True)
    p_reject.add_argument("--reason", required=True)
    add_common_args(p_reject)

    p_release = subparsers.add_parser("release")
    p_release.add_argument("--policy-id", required=True)
    add_common_args(p_release)

    p_expire = subparsers.add_parser("expire")
    p_expire.add_argument("--policy-id", required=True)
    add_common_args(p_expire)

    p_cancel = subparsers.add_parser("cancel")
    p_cancel.add_argument("--policy-id", required=True)
    p_cancel.add_argument("--reason", required=True)
    add_common_args(p_cancel)

    p_dashboard = subparsers.add_parser("dashboard")
    p_dashboard.add_argument("--seller")
    p_dashboard.add_argument("--env")
    add_common_args(p_dashboard)

    p_digest = subparsers.add_parser("digest")
    p_digest.add_argument("--type", choices=["active", "seller", "environment", "daily"], required=True)
    p_digest.add_argument("--seller")
    p_digest.add_argument("--env")
    p_digest.add_argument("--date")
    add_common_args(p_digest)

    args = parser.parse_args()

    if args.command == "scan": scan(args)
    elif args.command == "candidate-list": candidate_list(args)
    elif args.command == "list": policy_list(args)
    elif args.command == "show": show(args)
    elif args.command == "propose": propose(args)
    elif args.command == "approve": approve(args)
    elif args.command == "activate": activate(args)
    elif args.command == "reject": reject(args)
    elif args.command == "release": release(args)
    elif args.command == "expire": expire(args)
    elif args.command == "cancel": cancel(args)
    elif args.command == "dashboard": dashboard(args)
    elif args.command == "digest": digest(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
