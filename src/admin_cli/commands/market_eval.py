import argparse
from src.db.session import SessionLocal
from src.admin_cli.services.market_eval_ops_service import MarketEvalOpsService

def setup_market_eval_parser(subparsers):
    parser = subparsers.add_parser("market-eval", help="Market Evaluation operations")
    sub_commands = parser.add_subparsers(dest="action", help="Action to perform")
    
    evaluate_parser = sub_commands.add_parser("run", help="Run evaluation for a candidate")
    evaluate_parser.add_argument("candidate_id", type=str, help="Candidate ID to evaluate")

def handle_market_eval_command(args):
    with SessionLocal() as db:
        service = MarketEvalOpsService(db)
        if args.action == "run":
            service.evaluate_candidate(args.candidate_id)
        else:
            print("Unknown market-eval action")
