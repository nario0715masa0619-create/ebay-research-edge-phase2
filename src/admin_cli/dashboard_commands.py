import argparse
import json
import csv
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService

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
        if not results:
            print("No records found.")
            return
        keys = list(results[0].keys())
        header = " | ".join(f"{k:20}" for k in keys)
        print(header)
        print("-" * len(header))
        for row in results:
            print(" | ".join(f"{str(row.get(k, '')):20}"[:20] for k in keys))

def _get_date_range(args):
    from_date = datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc) if args.from_date else datetime.now(timezone.utc) - timedelta(days=7)
    to_date = datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc) if args.to_date else datetime.now(timezone.utc)
    
    if from_date > to_date:
        print("validation error: from_date cannot be after to_date", file=sys.stderr)
        sys.exit(1)
        
    return from_date, to_date

def handle_overview(args):
    service = ExecutionDashboardService()
    dr = _get_date_range(args)
    summary = service.get_overview_summary(dr)
    
    out = [{
        "total": summary.total_executions,
        "success_rate": summary.success_rate,
        "failure_count": summary.failed,
        "alert_count": summary.alert_count,
        "dry_run_count": summary.dry_run_count,
        "live_count": summary.live_count
    }]
    _output_results(out, args.format)

def handle_sellers(args):
    service = ExecutionDashboardService()
    dr = _get_date_range(args)
    
    rates = service.get_seller_failure_analysis(dr)
    # Get failure count by getting all attempts for that seller
    # For simplicity in this CLI, we will just show the rate and a dummy last_failure_at (or omit it)
    # as get_seller_failure_analysis returns Dict[seller, rate]
    
    out = []
    for seller, rate in rates.items():
        out.append({
            "seller": seller,
            "failure_rate": rate
        })
    _output_results(out, args.format)

def handle_errors(args):
    service = ExecutionDashboardService()
    dr = _get_date_range(args)
    top_errors = service.get_top_error_codes(limit=args.limit, date_range=dr)
    
    out = []
    for code, count in top_errors:
        out.append({
            "error_code": code,
            "count": count
        })
    _output_results(out, args.format)

def build_parser():
    parser = argparse.ArgumentParser(description="ops dashboard commands")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    subparsers = parser.add_subparsers(dest="subcommand")
    
    overview = subparsers.add_parser("overview")
    overview.add_argument("--from-date")
    overview.add_argument("--to-date")
    
    sellers = subparsers.add_parser("sellers")
    sellers.add_argument("--from-date")
    sellers.add_argument("--to-date")
    
    errors = subparsers.add_parser("errors")
    errors.add_argument("--from-date")
    errors.add_argument("--to-date")
    errors.add_argument("--limit", type=int, default=5)
    
    return parser

def main(args=None):
    parser = build_parser()
    parsed = parser.parse_args(args)
    if parsed.subcommand == "overview":
        handle_overview(parsed)
    elif parsed.subcommand == "sellers":
        handle_sellers(parsed)
    elif parsed.subcommand == "errors":
        handle_errors(parsed)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
