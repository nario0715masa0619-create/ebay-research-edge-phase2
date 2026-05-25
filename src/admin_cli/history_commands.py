import argparse
import json
import csv
import sys
from datetime import datetime
from typing import List, Dict, Any

from src.listing_execution.models.history_query import HistoryQuery, HistoryEventView
from src.listing_execution.services.execution_history_query_service import ExecutionHistoryQueryService
from src.listing_execution.services.execution_audit_timeline_service import ExecutionAuditTimelineService

def _output_results(results: List[Dict[str, Any]], fmt: str):
    if fmt == "json":
        print(json.dumps(results, default=str, indent=2))
    elif fmt == "csv":
        if not results:
            return
        writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    else:
        # Table format (simple implementation, ideally use tabulate or rich)
        if not results:
            print("No records found.")
            return
        keys = list(results[0].keys())
        header = " | ".join(f"{k:20}" for k in keys)
        print(header)
        print("-" * len(header))
        for row in results:
            print(" | ".join(f"{str(row.get(k, '')):20}"[:20] for k in keys))

def handle_recent(args):
    service = ExecutionHistoryQueryService()
    query = HistoryQuery(limit=args.limit)
    if args.dry_run_only:
        query.dry_run = True
    elif args.live_only:
        query.dry_run = False
        
    events = service.apply_filters(query)["items"]
    
    out = []
    for e in events:
        out.append({
            "event_type": e.event_type,
            "attempt_id": e.attempt_id,
            "listing_id": e.listing_id,
            "created_at": e.created_at,
            "dry_run": e.dry_run,
            "status": e.to_state or ""
        })
    _output_results(out, args.format)

def handle_show(args):
    timeline_service = ExecutionAuditTimelineService()
    events = timeline_service.build_attempt_timeline(args.attempt_id)
    
    if not events:
        print("not found")
        return
        
    out = []
    for e in events:
        out.append({
            "timestamp": e.created_at,
            "event_type": e.event_type,
            "from_state": e.from_state or "",
            "to_state": e.to_state or "",
            "error": e.error_code or e.error_message or ""
        })
    _output_results(out, args.format)

def handle_list(args):
    service = ExecutionHistoryQueryService()
    
    from_date = datetime.fromisoformat(args.from_date) if args.from_date else None
    to_date = datetime.fromisoformat(args.to_date) if args.to_date else None
    
    if from_date and to_date and from_date > to_date:
        print("validation error: from_date cannot be after to_date", file=sys.stderr)
        sys.exit(1)
        
    query = HistoryQuery(
        seller_account_id=args.seller,
        environment=args.environment,
        event_type=args.event_type
    )
    if from_date and to_date:
        query.date_range = (from_date, to_date)
        
    # Example of invalid environment reject
    if args.environment and args.environment not in ("US", "UK", "sandbox", "production"):
        print("reject: invalid environment", file=sys.stderr)
        sys.exit(1)
        
    events = service.apply_filters(query)["items"]
    
    out = []
    for e in events:
        # seller / environment would require joining or resolving if not on event view, 
        # but since HistoryEventView doesn't have them directly, we will output what we can 
        # or we could fetch attempt data. For now, we output listing_id and event_type
        out.append({
            "event_type": e.event_type,
            "listing_id": e.listing_id,
            "attempt_id": e.attempt_id,
            "created_at": e.created_at
        })
    _output_results(out, args.format)

def build_parser():
    parser = argparse.ArgumentParser(description="ops history commands")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    subparsers = parser.add_subparsers(dest="subcommand")
    
    recent = subparsers.add_parser("recent")
    recent.add_argument("--limit", type=int, default=20)
    recent.add_argument("--dry-run-only", action="store_true")
    recent.add_argument("--live-only", action="store_true")
    
    show = subparsers.add_parser("show")
    show.add_argument("--attempt-id", required=True)
    
    lst = subparsers.add_parser("list")
    lst.add_argument("--seller")
    lst.add_argument("--environment")
    lst.add_argument("--from-date")
    lst.add_argument("--to-date")
    lst.add_argument("--event-type")
    
    return parser

def main(args=None):
    parser = build_parser()
    parsed = parser.parse_args(args)
    if parsed.subcommand == "recent":
        handle_recent(parsed)
    elif parsed.subcommand == "show":
        handle_show(parsed)
    elif parsed.subcommand == "list":
        handle_list(parsed)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
