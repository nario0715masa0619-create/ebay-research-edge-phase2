import argparse
import sys
from .models import CliExecutionContext, CliCommandResult
from .output_formatter import CliOutputFormatter
from .bootstrap import AdminCliBootstrap

def main():
    parser = argparse.ArgumentParser(description="eBay Research Edge Admin/Ops CLI")
    parser.add_argument("--format", choices=["table", "json", "text"], default="table")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--confirm", action="store_true", default=False)
    
    subparsers = parser.add_subparsers(dest="group", help="Command groups")
    
    # Jobs
    jobs_p = subparsers.add_parser("jobs")
    jobs_sub = jobs_p.add_subparsers(dest="command")
    jobs_sub.add_parser("list")
    run_p = jobs_sub.add_parser("run")
    run_p.add_argument("job_name")
    run_p.add_argument("--limit", type=int)
    
    # Scheduler
    sched_p = subparsers.add_parser("scheduler")
    sched_sub = sched_p.add_subparsers(dest="command")
    sched_sub.add_parser("status")
    sched_sub.add_parser("run-once")
    
    # Candidates
    cand_p = subparsers.add_parser("candidates")
    cand_sub = cand_p.add_subparsers(dest="command")
    cand_list = cand_sub.add_parser("list")
    cand_list.add_argument("--status")
    cand_list.add_argument("--limit", type=int, default=20)
    cand_show = cand_sub.add_parser("show")
    cand_show.add_argument("--sku", required=True)

    # Listings
    list_p = subparsers.add_parser("listings")
    list_sub = list_p.add_subparsers(dest="command")
    list_sub.add_parser("list")
    sync_p = list_sub.add_parser("sync")
    sync_p.add_argument("--sku", required=True)
    
    # Review
    review_p = subparsers.add_parser("review")
    review_sub = review_p.add_subparsers(dest="command")
    review_sub.add_parser("list")
    
    # Evidence
    evid_p = subparsers.add_parser("evidence")
    evid_sub = evid_p.add_subparsers(dest="command")
    evid_list = evid_sub.add_parser("list")
    evid_list.add_argument("--candidate-id", required=True)
    evid_show = evid_sub.add_parser("show")
    evid_show.add_argument("--evidence-id", required=True)
    
    # Events
    event_p = subparsers.add_parser("events")
    event_sub = event_p.add_subparsers(dest="command")
    event_sub.add_parser("recent")
    event_show = event_sub.add_parser("show")
    event_show.add_argument("--event-id", required=True)
    
    # JobRuns
    jr_p = subparsers.add_parser("jobruns")
    jr_sub = jr_p.add_subparsers(dest="command")
    jr_sub.add_parser("recent")
    jr_show = jr_sub.add_parser("show")
    jr_show.add_argument("--run-id", required=True)
    
    # Doctor
    subparsers.add_parser("doctor")
    
    # Config
    config_p = subparsers.add_parser("config")
    config_sub = config_p.add_subparsers(dest="command")
    config_sub.add_parser("validate")
    
    args = parser.parse_args()
    
    if not args.group:
        parser.print_help()
        return

    # Bootstrap
    app = AdminCliBootstrap.bootstrap()
    
    context = CliExecutionContext(
        command_path=f"{args.group} {args.command}" if hasattr(args, "command") else args.group,
        output_format=args.format,
        dry_run=args.dry_run,
        confirm=args.confirm,
        limit=getattr(args, "limit", None)
    )
    
    # Simple dispatcher (in v0.1 we can just call services directly here or via a registry)
    # I'll use a simple if-else for now to keep it straightforward
    
    result = None
    try:
        if args.group == "jobs":
            if args.command == "list":
                records = app.job_service.list_jobs()
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "run":
                result = app.job_service.run_job(args.job_name, limit=args.limit, dry_run=args.dry_run)
        
        elif args.group == "scheduler":
            if args.command == "status":
                status = app.scheduler_service.get_status()
                result = CliCommandResult(command_path=context.command_path, summary=status)
            elif args.command == "run-once":
                result = app.scheduler_service.run_once(dry_run=args.dry_run)
        
        elif args.group == "candidates":
            if args.command == "list":
                records = app.candidate_service.list_candidates(status=args.status, limit=args.limit)
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "show":
                detail = app.candidate_service.get_candidate_detail(args.sku)
                if detail:
                    result = CliCommandResult(command_path=context.command_path, summary=detail)
                else:
                    result = CliCommandResult(command_path=context.command_path, status="error", errors=["Candidate not found."], exit_code=2)
        
        elif args.group == "listings":
            if args.command == "list":
                records = app.listing_service.list_listings()
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "sync":
                result = app.listing_service.sync_listing(args.sku, dry_run=args.dry_run)
        
        elif args.group == "review":
            if args.command == "list":
                records = app.review_service.list_review_queue()
                result = CliCommandResult(command_path=context.command_path, records=records)
        
        elif args.group == "evidence":
            if args.command == "list":
                records = app.evidence_service.list_by_candidate(args.candidate_id)
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "show":
                detail = app.evidence_service.get_detail(args.evidence_id)
                result = CliCommandResult(command_path=context.command_path, summary=detail or {"error": "Not found"})
        
        elif args.group == "events":
            if args.command == "recent":
                records = app.event_service.list_recent()
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "show":
                detail = app.event_service.get_detail(args.event_id)
                result = CliCommandResult(command_path=context.command_path, summary=detail or {"error": "Not found"})
        
        elif args.group == "jobruns":
            if args.command == "recent":
                records = app.jobrun_service.list_recent()
                result = CliCommandResult(command_path=context.command_path, records=records)
            elif args.command == "show":
                detail = app.jobrun_service.get_detail(args.run_id)
                result = CliCommandResult(command_path=context.command_path, summary=detail or {"error": "Not found"})

        elif args.group == "doctor":
            health = app.doctor_service.check_health()
            result = CliCommandResult(command_path=context.command_path, summary=health, status=health["overall"])
            
        elif args.group == "config":
            if args.command == "validate":
                report = app.config_service.validate()
                result = CliCommandResult(command_path=context.command_path, summary={"status": report["status"]}, records=[{"key": k, **v} for k, v in report["checks"].items()])
            
    except Exception as e:
        result = CliCommandResult(command_path=context.command_path, status="error", errors=[str(e)], exit_code=5)

    if result:
        formatter = CliOutputFormatter()
        print(formatter.format(result, fmt=args.format))
        sys.exit(result.exit_code)

if __name__ == "__main__":
    main()
