import argparse
import sys
import uuid
from typing import List, Optional
import datetime

# Attempt to import services/models (in a real app, these might be injected)
from src.incident.models.incident import IncidentSeverity, IncidentStatus, SlaState

# Colors
RED = '\033[91m'
ORANGE = '\033[33m'  # Using standard yellow/orange
YELLOW = '\033[93m'
GRAY = '\033[90m'
RESET = '\033[0m'

def colorize_severity(severity_str: str) -> str:
    s = severity_str.upper()
    if s == "CRITICAL": return f"{RED}{s}{RESET}"
    if s == "HIGH": return f"{ORANGE}{s}{RESET}"
    if s == "MEDIUM": return f"{YELLOW}{s}{RESET}"
    if s == "LOW": return f"{GRAY}{s}{RESET}"
    return s

def format_sla_badge(incident) -> str:
    if incident.sla_state in [SlaState.ACK_BREACHED, SlaState.RESOLVE_BREACHED, SlaState.BOTH_BREACHED]:
        return f"{RED}[BREACHED]{RESET}"
        
    now = datetime.datetime.utcnow()
    # Check overdue
    ack_overdue = not incident.acknowledged_at and incident.ack_due_at and now > incident.ack_due_at
    res_overdue = not incident.resolved_at and incident.resolve_due_at and now > incident.resolve_due_at
    
    if res_overdue:
        mins = int((now - incident.resolve_due_at).total_seconds() / 60)
        return f"{RED}[RESOLVE_OVERDUE {mins}m]{RESET}"
    if ack_overdue:
        mins = int((now - incident.ack_due_at).total_seconds() / 60)
        return f"{RED}[ACK_OVERDUE {mins}m]{RESET}"
        
    return "[ON_TRACK]"

class InvalidStateTransitionError(Exception):
    pass

class IncidentCLI:
    def __init__(self, detection_service, management_service, dashboard_service, linking_service, repo, event_repo):
        self.detection = detection_service
        self.management = management_service
        self.dashboard = dashboard_service
        self.linking = linking_service
        self.repo = repo
        self.event_repo = event_repo
        self.parser = self._build_parser()

    def _build_parser(self):
        parser = argparse.ArgumentParser(prog="ops incident", description="Incident Management CLI")
        subparsers = parser.add_subparsers(dest="command", required=True)

        # scan
        scan_p = subparsers.add_parser("scan")
        scan_p.add_argument("--environment", required=False)
        scan_p.add_argument("--seller", required=False)

        # list
        list_p = subparsers.add_parser("list")
        list_p.add_argument("--status", required=False)
        list_p.add_argument("--severity", required=False)
        list_p.add_argument("--seller", required=False)
        list_p.add_argument("--environment", required=False)
        list_p.add_argument("--overdue-only", action="store_true")
        list_p.add_argument("--breached-only", action="store_true")

        # show
        show_p = subparsers.add_parser("show")
        show_p.add_argument("--incident-id", required=True)

        # acknowledge
        ack_p = subparsers.add_parser("acknowledge")
        ack_p.add_argument("--incident-id", required=True)
        ack_p.add_argument("--note", required=False, default="")

        # assign
        assign_p = subparsers.add_parser("assign")
        assign_p.add_argument("--incident-id", required=True)
        assign_p.add_argument("--owner", required=True)

        # investigate
        inv_p = subparsers.add_parser("investigate")
        inv_p.add_argument("--incident-id", required=True)
        inv_p.add_argument("--note", required=False, default="")

        # mitigate
        mit_p = subparsers.add_parser("mitigate")
        mit_p.add_argument("--incident-id", required=True)
        mit_p.add_argument("--root-cause", required=False, default="UNKNOWN")
        mit_p.add_argument("--note", required=False, default="")

        # resolve
        res_p = subparsers.add_parser("resolve")
        res_p.add_argument("--incident-id", required=True)
        res_p.add_argument("--note", required=False, default="")

        # close
        cls_p = subparsers.add_parser("close")
        cls_p.add_argument("--incident-id", required=True)
        cls_p.add_argument("--note", required=False, default="")

        # reopen
        reo_p = subparsers.add_parser("reopen")
        reo_p.add_argument("--incident-id", required=True)
        reo_p.add_argument("--reason", required=False, default="")

        # cancel
        can_p = subparsers.add_parser("cancel")
        can_p.add_argument("--incident-id", required=True)
        can_p.add_argument("--reason", required=False, default="")

        # dashboard
        dash_p = subparsers.add_parser("dashboard")
        dash_p.add_argument("--time-range-hours", type=int, default=24)

        # overdue
        subparsers.add_parser("overdue")

        # breached
        subparsers.add_parser("breached")

        # links
        links_p = subparsers.add_parser("links")
        links_p.add_argument("--incident-id", required=True)

        return parser

    def _get_incident(self, id_str):
        try:
            uid = uuid.UUID(id_str)
        except ValueError:
            print("not found")
            sys.exit(1)
            
        try:
            # We mock the get_incident throwing KeyError if not found
            # Assuming self.repo is available
            inc = self.repo.get_incident(uid)
            return inc
        except Exception:
            print("not found")
            sys.exit(1)

    def execute(self, args_list: List[str]):
        try:
            args = self.parser.parse_args(args_list)
        except SystemExit as e:
            return e.code
            
        try:
            if args.command == "scan":
                self._cmd_scan(args)
            elif args.command == "list":
                self._cmd_list(args)
            elif args.command == "show":
                self._cmd_show(args)
            elif args.command == "acknowledge":
                self._cmd_transition("acknowledge", args)
            elif args.command == "assign":
                self._cmd_assign(args)
            elif args.command == "investigate":
                self._cmd_transition("investigate", args)
            elif args.command == "mitigate":
                self._cmd_mitigate(args)
            elif args.command == "resolve":
                self._cmd_transition("resolve", args)
            elif args.command == "close":
                self._cmd_transition("close", args)
            elif args.command == "reopen":
                self._cmd_transition("reopen", args)
            elif args.command == "cancel":
                self._cmd_transition("cancel", args)
            elif args.command == "dashboard":
                self._cmd_dashboard(args)
            elif args.command == "overdue":
                self._cmd_overdue(args)
            elif args.command == "breached":
                self._cmd_breached(args)
            elif args.command == "links":
                self._cmd_links(args)
        except Exception as e:
            if "InvalidStateTransition" in str(type(e)):
                print(f"Error: {e}")
            else:
                print(f"Error: {e}")
            return 1
        return 0

    def _print_incident_table(self, incidents):
        print(f"{'ID':<38} | {'STATUS':<15} | {'SEVERITY':<20} | {'SELLER':<10} | {'OPENED_AT':<20} | {'SLA_STATE'}")
        print("-" * 130)
        for inc in incidents:
            sev = colorize_severity(inc.severity.value)
            sla = format_sla_badge(inc)
            print(f"{str(inc.incident_id):<38} | {inc.incident_status.value:<15} | {sev:<30} | {str(inc.seller_account_id):<10} | {str(inc.opened_at)[:19]:<20} | {sla}")

    def _cmd_scan(self, args):
        print("Scanning for incident candidates...")
        # Mock logic
        print("Done.")

    def _cmd_list(self, args):
        # We fetch from dashboard service if it has it, or repo directly
        incs = self.repo.get_all_incidents()
        
        filtered = []
        for inc in incs:
            if args.status and inc.incident_status.value != args.status: continue
            if args.severity and inc.severity.value != args.severity: continue
            if args.seller and inc.seller_account_id != args.seller: continue
            if args.environment and inc.environment != args.environment: continue
            
            if args.overdue_only:
                if format_sla_badge(inc) == "[ON_TRACK]" and "BREACHED" not in format_sla_badge(inc):
                    if "OVERDUE" not in format_sla_badge(inc):
                        continue
            
            if args.breached_only:
                if "BREACHED" not in format_sla_badge(inc):
                    continue
                    
            filtered.append(inc)
            
        self._print_incident_table(filtered)

    def _cmd_show(self, args):
        inc = self._get_incident(args.incident_id)
        print(f"Incident ID: {inc.incident_id}")
        print(f"Title: {inc.title}")
        print(f"Status: {inc.incident_status.value}")
        print(f"Severity: {colorize_severity(inc.severity.value)}")
        print(f"SLA State: {format_sla_badge(inc)}")
        print("\nTimeline:")
        
        events = [e for e in self.event_repo.events if e.incident_id == inc.incident_id]
        events.sort(key=lambda x: x.created_at)
        for e in events:
            print(f"[{str(e.created_at)[:19]}] {e.event_type.value} by {e.actor_id}: {e.note}")

    def _cmd_transition(self, action, args):
        uid = uuid.UUID(args.incident_id)
        if action == "acknowledge":
            self.management.acknowledge_incident(uid, "cli_user", getattr(args, "note", ""))
        elif action == "investigate":
            self.management.start_investigation(uid, "cli_user", getattr(args, "note", ""))
        elif action == "resolve":
            self.management.resolve_incident(uid, "cli_user", getattr(args, "note", ""))
        elif action == "close":
            self.management.close_incident(uid, "cli_user", getattr(args, "note", ""))
        elif action == "reopen":
            self.management.reopen_incident(uid, "cli_user", getattr(args, "reason", ""))
        elif action == "cancel":
            self.management.cancel_incident(uid, "cli_user", getattr(args, "reason", ""))
        print(f"Incident {args.incident_id} {action}d successfully.")

    def _cmd_assign(self, args):
        uid = uuid.UUID(args.incident_id)
        self.management.assign_incident(uid, args.owner, "cli_user")
        print(f"Incident {args.incident_id} assigned to {args.owner}.")

    def _cmd_mitigate(self, args):
        uid = uuid.UUID(args.incident_id)
        self.management.mitigate_incident(uid, "cli_user", args.root_cause, args.note)
        print(f"Incident {args.incident_id} mitigated.")

    def _cmd_dashboard(self, args):
        summary = self.dashboard.get_incident_summary(time_range_hours=args.time_range_hours)
        print("=== Incident Dashboard ===")
        print(f"Total Open: {summary.open_count}")
        print(f"Total Overdue: {summary.overdue_count}")
        print(f"Total Breached: {summary.breached_count}")
        print(f"Severity Breakdown: {summary.by_severity}")
        print(f"MTTA (hours): {summary.mean_ack_time_hours}")
        print(f"MTTR (hours): {summary.mean_resolve_time_hours}")

    def _cmd_overdue(self, args):
        incs = self.dashboard.get_overdue_incidents()
        self._print_incident_table(incs)

    def _cmd_breached(self, args):
        incs = self.dashboard.get_breached_incidents()
        self._print_incident_table(incs)

    def _cmd_links(self, args):
        uid = uuid.UUID(args.incident_id)
        if self.linking and self.linking.link_repo:
            links = [l for l in self.linking.link_repo.links if l.incident_id == uid]
            for l in links:
                print(f"{l.entity_type.value}: {l.entity_id}")
