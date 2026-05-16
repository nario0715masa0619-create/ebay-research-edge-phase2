import argparse
import sys
from .models import CliExecutionContext, CliCommandResult
from .output_formatter import CliOutputFormatter
from .bootstrap import AdminCliBootstrap

from .commands.jobs import JobCommands
from .commands.scheduler import SchedulerCommands
from .commands.candidates import CandidateCommands
from .commands.listings import ListingCommands
from .commands.review import ReviewCommands
from .commands.evidence import EvidenceCommands
from .commands.events import EventCommands
from .commands.jobruns import JobRunCommands
from .commands.doctor import DoctorCommands
from .commands.config import ConfigCommands

def main():
    parser = argparse.ArgumentParser(description="eBay Research Edge Admin/Ops CLI")
    parser.add_argument("--format", choices=["table", "json", "text"], default="table")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--confirm", action="store_true", default=False)
    parser.add_argument("--force-recheck", action="store_true", default=False)
    
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
    cand_list.add_argument("--limit", type=int)
    cand_show = cand_sub.add_parser("show")
    cand_show.add_argument("--sku", required=True)

    # Listings
    list_p = subparsers.add_parser("listings")
    list_sub = list_p.add_subparsers(dest="command")
    list_sub.add_parser("list")
    sync_p = list_sub.add_parser("sync")
    sync_p.add_argument("--sku", required=True)
    withdraw_p = list_sub.add_parser("withdraw")
    withdraw_p.add_argument("--sku", required=True)
    
    # Review
    review_p = subparsers.add_parser("review")
    review_sub = review_p.add_subparsers(dest="command")
    review_l = review_sub.add_parser("list")
    review_l.add_argument("--reason")
    
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
        command_path=f"{args.group} {args.command}" if hasattr(args, "command") and args.command else args.group,
        output_format=args.format,
        dry_run=args.dry_run,
        confirm=args.confirm,
        force_recheck=args.force_recheck,
        limit=getattr(args, "limit", None)
    )
    
    result = None
    try:
        if args.group == "jobs":
            cmd = JobCommands(app.job_service)
            if args.command == "list": result = cmd.list(context)
            elif args.command == "run": result = cmd.run(context, args.job_name, limit=args.limit)
        
        elif args.group == "scheduler":
            cmd = SchedulerCommands(app.scheduler_service)
            if args.command == "status": result = cmd.status(context)
            elif args.command == "run-once": result = cmd.run_once(context)
        
        elif args.group == "candidates":
            cmd = CandidateCommands(app.candidate_service)
            if args.command == "list": result = cmd.list(context, status=args.status)
            elif args.command == "show": result = cmd.show(context, args.sku)
        
        elif args.group == "listings":
            cmd = ListingCommands(app.listing_service)
            if args.command == "list": result = cmd.list(context)
            elif args.command == "sync": result = cmd.sync(context, args.sku)
            elif args.command == "withdraw": result = cmd.withdraw(context, args.sku)
        
        elif args.group == "review":
            cmd = ReviewCommands(app.review_service)
            if args.command == "list": result = cmd.list(context, reason=args.reason)
        
        elif args.group == "evidence":
            cmd = EvidenceCommands(app.evidence_service)
            if args.command == "list": result = cmd.list(context, args.candidate_id)
            elif args.command == "show": result = cmd.show(context, args.evidence_id)
        
        elif args.group == "events":
            cmd = EventCommands(app.event_service)
            if args.command == "recent": result = cmd.recent(context)
            elif args.command == "show": result = cmd.show(context, args.event_id)
        
        elif args.group == "jobruns":
            cmd = JobRunCommands(app.jobrun_service)
            if args.command == "recent": result = cmd.recent(context)
            elif args.command == "show": result = cmd.show(context, args.run_id)

        elif args.group == "doctor":
            cmd = DoctorCommands(app.doctor_service)
            result = cmd.run(context)
            
        elif args.group == "config":
            cmd = ConfigCommands(app.config_service)
            if args.command == "validate": result = cmd.validate(context)
            
    except Exception as e:
        import traceback
        if context.verbose: traceback.print_exc()
        result = CliCommandResult(command_path=context.command_path, status="error", errors=[str(e)], exit_code=5)

    if result:
        formatter = CliOutputFormatter()
        print(formatter.format(result, fmt=args.format))
        sys.exit(result.exit_code)

if __name__ == "__main__":
    main()
