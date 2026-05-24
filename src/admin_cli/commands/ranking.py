import argparse
from src.db.session import SessionLocal
from src.admin_cli.services.ranking_ops_service import RankingOpsService

def setup_ranking_parser(subparsers):
    parser = subparsers.add_parser("ranking", help="Ranking / Listing Decision operations")
    sub_commands = parser.add_subparsers(dest="action", help="Action to perform")
    
    run_parser = sub_commands.add_parser("run", help="Run ranking decision for a candidate")
    run_parser.add_argument("candidate_id", type=str, help="Candidate ID to evaluate")

def handle_ranking_command(args):
    with SessionLocal() as db:
        service = RankingOpsService(db)
        if args.action == "run":
            service.run_ranking(args.candidate_id)
        else:
            print("Unknown ranking action")
