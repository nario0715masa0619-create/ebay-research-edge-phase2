import argparse
from src.db.session import SessionLocal
from src.admin_cli.services.profitability_ops_service import ProfitabilityOpsService

def setup_profitability_parser(subparsers):
    parser = subparsers.add_parser("profitability", help="Profitability Scoring operations")
    sub_commands = parser.add_subparsers(dest="action", help="Action to perform")
    
    run_parser = sub_commands.add_parser("run", help="Run scoring for a candidate")
    run_parser.add_argument("candidate_id", type=str, help="Candidate ID to score")

def handle_profitability_command(args):
    with SessionLocal() as db:
        service = ProfitabilityOpsService(db)
        if args.action == "run":
            service.run_scoring(args.candidate_id)
        else:
            print("Unknown profitability action")
