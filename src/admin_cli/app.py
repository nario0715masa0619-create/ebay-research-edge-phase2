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
from .commands.notifications import NotificationCommands
from .commands.sellers import SellerCommands
from .commands.escalation import EscalationCommands
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
    
    # Notifications
    ntf_p = subparsers.add_parser("notifications")
    ntf_sub = ntf_p.add_subparsers(dest="command")
    
    ntf_recent = ntf_sub.add_parser("recent")
    ntf_recent.add_argument("--limit", type=int, default=50)
    ntf_recent.add_argument("--severity")
    ntf_recent.add_argument("--channel")
    ntf_recent.add_argument("--event-type")
    
    ntf_failed = ntf_sub.add_parser("failed")
    ntf_failed.add_argument("--limit", type=int, default=50)
    ntf_failed.add_argument("--channel")
    ntf_failed.add_argument("--event-type")
    
    ntf_show = ntf_sub.add_parser("show")
    ntf_show.add_argument("history_id")
    
    ntf_by_sku = ntf_sub.add_parser("by-sku")
    ntf_by_sku.add_argument("--sku", required=True)
    ntf_by_sku.add_argument("--limit", type=int, default=20)
    
    ntf_by_event = ntf_sub.add_parser("by-event")
    ntf_by_event.add_argument("--event-type", required=True)
    ntf_by_event.add_argument("--limit", type=int, default=20)
    
    ntf_resend = ntf_sub.add_parser("resend")
    ntf_resend.add_argument("--history-id")
    ntf_resend.add_argument("--event-id")
    ntf_resend.add_argument("--channel")
    ntf_resend.add_argument("--force-resend", action="store_true")
    
    ntf_test = ntf_sub.add_parser("test")
    ntf_test.add_argument("--channel", required=True)
    ntf_test.add_argument("--title")
    ntf_test.add_argument("--summary")
    
    ntf_rules = ntf_sub.add_parser("rules")
    ntf_rules_sub = ntf_rules.add_subparsers(dest="subcommand")
    ntf_rules_sub.add_parser("list")
    ntf_rules_show = ntf_rules_sub.add_parser("show")
    ntf_rules_show.add_argument("rule_name")
    
    ntf_rules_for = ntf_rules_sub.add_parser("for-event")
    ntf_rules_for.add_argument("--event-type", required=True)
    ntf_rules_for.add_argument("--severity", default="info")
    
    ntf_sub.add_parser("channels")
    
    ntf_stats = ntf_sub.add_parser("stats")
    ntf_stats.add_argument("--hours", type=int, default=24)
    ntf_stats.add_argument("--event-type")
    
    # Escalation
    esc_p = subparsers.add_parser("escalation")
    esc_sub = esc_p.add_subparsers(dest="command")
    
    esc_sub.add_parser("active")
    
    esc_recent = esc_sub.add_parser("recent")
    esc_recent.add_argument("--limit", type=int, default=50)
    
    esc_show = esc_sub.add_parser("show")
    esc_show.add_argument("state_id")
    
    esc_ack = esc_sub.add_parser("ack")
    esc_ack.add_argument("state_id")
    esc_ack.add_argument("--note")
    
    esc_resolve = esc_sub.add_parser("resolve")
    esc_resolve.add_argument("state_id")
    esc_resolve.add_argument("--note")
    
    esc_silence = esc_sub.add_parser("silence")
    esc_silence.add_argument("state_id")
    esc_silence.add_argument("--hours", type=int, default=24)
    esc_silence.add_argument("--note")
    
    esc_unsilence = esc_sub.add_parser("unsilence")
    esc_unsilence.add_argument("state_id")
    esc_unsilence.add_argument("--note")
    
    esc_sub.add_parser("stats")
    esc_sub.add_parser("policies")
    
    esc_sub.add_parser("breached")
    
    esc_aging = esc_sub.add_parser("aging")
    esc_aging.add_argument("--bucket", required=True)
    
    esc_tl = esc_sub.add_parser("timeline")
    esc_tl.add_argument("state_id")
    
    # Notes
    esc_note = esc_sub.add_parser("notes")
    esc_note_sub = esc_note.add_subparsers(dest="subcommand")
    esc_note_list = esc_note_sub.add_parser("list")
    esc_note_list.add_argument("state_id")
    esc_note_add = esc_note_sub.add_parser("add")
    esc_note_add.add_argument("state_id")
    esc_note_add.add_argument("--body", required=True)
    
    # Bulk actions
    esc_bulk_ack = esc_sub.add_parser("bulk-ack")
    esc_bulk_ack.add_argument("--state-ids", required=True, help="comma-separated")
    
    esc_bulk_res = esc_sub.add_parser("bulk-resolve")
    esc_bulk_res.add_argument("--state-ids", required=True)
    
    esc_bulk_sil = esc_sub.add_parser("bulk-silence")
    esc_bulk_sil.add_argument("--state-ids", required=True)
    esc_bulk_sil.add_argument("--hours", type=int, default=24)
    
    # Maintenance
    maint_p = esc_sub.add_parser("maintenance")
    maint_sub = maint_p.add_subparsers(dest="subcommand")
    maint_sub.add_parser("list")
    maint_add = maint_sub.add_parser("add")
    maint_add.add_argument("--starts", required=True, help="ISO format")
    maint_add.add_argument("--ends", required=True, help="ISO format")
    maint_add.add_argument("--action", default="suppress_all")
    maint_add.add_argument("--seller")
    maint_add.add_argument("--env")
    maint_add.add_argument("--event")
    
    maint_rm = maint_sub.add_parser("remove")
    maint_rm.add_argument("window_id")
    
    # Ops (Sellers/Environments)
    ops_p = subparsers.add_parser("ops")
    ops_sub = ops_p.add_subparsers(dest="subgroup")
    
    # Ops Sellers
    seller_p = ops_sub.add_parser("sellers")
    seller_sub = seller_p.add_subparsers(dest="command")
    seller_sub.add_parser("list")
    
    seller_bind = seller_sub.add_parser("bindings")
    seller_bind.add_argument("--seller-account-id")
    
    seller_act = seller_sub.add_parser("activate")
    seller_act.add_argument("--seller-account-id", required=True)
    seller_act.add_argument("--environment", required=True)
    
    seller_doc = seller_sub.add_parser("doctor")
    seller_doc.add_argument("--seller-account-id", required=True)
    
    seller_pol = seller_sub.add_parser("policies")
    seller_pol.add_argument("--seller-account-id", required=True)
    seller_pol.add_argument("--marketplace", required=True)
    
    seller_loc = seller_sub.add_parser("locations")
    seller_loc.add_argument("--seller-account-id", required=True)
    seller_loc.add_argument("--location-key", required=True)
    
    # Ops Environments
    env_p = ops_sub.add_parser("environments")
    env_sub = env_p.add_subparsers(dest="command")
    env_sub.add_parser("list")
    
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
            
        elif args.group == "notifications":
            cmd = NotificationCommands(app.notification_service)
            if args.command == "recent": result = cmd.recent(context, limit=args.limit, severity=args.severity, channel=args.channel, event_type=args.event_type)
            elif args.command == "failed": result = cmd.failed(context, limit=args.limit, channel=args.channel, event_type=args.event_type)
            elif args.command == "show": result = cmd.show(context, args.history_id)
            elif args.command == "by-sku": result = cmd.by_sku(context, args.sku, limit=args.limit)
            elif args.command == "by-event": result = cmd.by_event(context, args.event_type, limit=args.limit)
            elif args.command == "resend": result = cmd.resend(context, history_id=args.history_id, event_id=args.event_id, channel=args.channel, force=args.force_resend)
            elif args.command == "test": result = cmd.test(context, args.channel, title=args.title, summary=args.summary)
            elif args.command == "rules":
                if args.subcommand == "list": result = cmd.list_rules(context)
                elif args.subcommand == "show": result = cmd.show_rule(context, args.rule_name)
                elif args.subcommand == "for-event": result = cmd.rules_for_event(context, args.event_type, severity=args.severity)
            elif args.command == "channels": result = cmd.channels(context)
            elif args.command == "stats": result = cmd.stats(context, hours=args.hours, event_type=args.event_type)
        elif args.group == "escalation":
            cmd = EscalationCommands(app.escalation_service)
            if args.command == "active": result = cmd.active(context)
            elif args.command == "recent": result = cmd.recent(context, limit=args.limit)
            elif args.command == "show": result = cmd.show(context, args.state_id)
            elif args.command == "ack": result = cmd.ack(context, args.state_id, note=getattr(args, "note", None))
            elif args.command == "resolve": result = cmd.resolve(context, args.state_id, note=getattr(args, "note", None))
            elif args.command == "silence": result = cmd.silence(context, args.state_id, hours=args.hours, note=getattr(args, "note", None))
            elif args.command == "unsilence": result = cmd.unsilence(context, args.state_id, note=getattr(args, "note", None))
            elif args.command == "stats": result = cmd.stats(context)
            elif args.command == "policies": result = cmd.policies(context)
            elif args.command == "breached": result = cmd.breached(context)
            elif args.command == "aging": result = cmd.aging(context, args.bucket)
            elif args.command == "timeline": result = cmd.timeline(context, args.state_id)
            elif args.command == "notes":
                if args.subcommand == "list": result = cmd.list_notes(context, args.state_id)
                elif args.subcommand == "add": result = cmd.add_note(context, args.state_id, args.body)
            elif args.command == "bulk-ack": result = cmd.bulk_ack(context, args.state_ids)
            elif args.command == "bulk-resolve": result = cmd.bulk_resolve(context, args.state_ids)
            elif args.command == "bulk-silence": result = cmd.bulk_silence(context, args.state_ids, args.hours)
            elif args.command == "maintenance":
                if args.subcommand == "list": result = cmd.maintenance_list(context)
                elif args.subcommand == "add": result = cmd.maintenance_add(context, args.starts, args.ends, args.action, getattr(args, "seller", None), getattr(args, "env", None), getattr(args, "event", None))
                elif args.subcommand == "remove": result = cmd.maintenance_remove(context, args.window_id)
            
        elif args.group == "ops":
            cmd = SellerCommands(app.seller_ops, app.seller_doctor, app.seller_snapshot_ops)
            if args.subgroup == "sellers":
                if args.command == "list": result = cmd.list_sellers(context)
                elif args.command == "bindings": result = cmd.list_bindings(context, seller_account_id=args.seller_account_id)
                elif args.command == "activate": result = cmd.activate_binding(context, args.seller_account_id, args.environment)
                elif args.command == "doctor": result = cmd.doctor_seller(context, args.seller_account_id)
                elif args.command == "policies": result = cmd.show_policies(context, args.seller_account_id, args.marketplace)
                elif args.command == "locations": result = cmd.show_locations(context, args.seller_account_id, args.location_key)
            elif args.subgroup == "environments":
                if args.command == "list": result = cmd.list_environments(context)
            
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
