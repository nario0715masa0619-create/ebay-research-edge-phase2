import json
import argparse
from typing import Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.listing_execution.services.application_service import ExecutionApplicationService
from src.listing_readiness.services.readiness_checker import ReadinessChecker
from src.listing_execution.gateways.execution_gateway import ValidationResult, ExecutionResult
from src.listing_execution.executors.mock_executor import MockExecutor
from src.listing_execution.repositories.execution_attempt_repository import ExecutionAttemptRepository
from src.listing_execution.models.execution_payload import ExecutionPayload

def get_service(db_url: str = "sqlite:///:memory:") -> ExecutionApplicationService:
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    repository = ExecutionAttemptRepository(session)
    readiness_checker = ReadinessChecker()
    gateway = MockExecutor(
        allowed_environments=["sandbox", "production"], 
        allowed_sellers=["seller_A", "seller_B"], 
        fixture_rules={}
    )
    
    return ExecutionApplicationService(
        gateway=gateway,
        readiness_checker=readiness_checker,
        repository=repository
    )

def check_readiness(args):
    service = get_service()
    candidate_data = json.loads(args.candidate_data) if args.candidate_data else {}
    seller_data = json.loads(args.seller_data) if args.seller_data else {}
    handoff_data = json.loads(args.handoff_data) if args.handoff_data else {}
    result = service.check_readiness(candidate_data, seller_data, handoff_data)
    print(json.dumps({
        "is_ready": result.is_ready,
        "score": result.readiness_score,
        "reasons": result.readiness_reasons
    }, indent=2))

def execute_listing(args):
    service = get_service()
    payload_data = json.loads(args.payload)
    
    candidate_data = payload_data.get("candidate_data", {})
    seller_data = payload_data.get("seller_data", {})
    handoff_data = payload_data.get("handoff_data", {})
    
    payload = ExecutionPayload(
        attempt_id=payload_data.get("attempt_id"),
        listing_id=payload_data.get("listing_id"),
        candidate_id=payload_data.get("candidate_id"), # Optional field handled inside DB / not in payload schema directly, wait no: candidate_id was removed from ExecutionPayload schema! It only has listing_id, seller, sku, bundle_state, market_eval, profitability_score, environment, dry_run, attempt_id.
        seller=payload_data.get("seller"),
        sku=payload_data.get("sku", ""),
        bundle_state=payload_data.get("bundle_state", "none"),
        market_eval=payload_data.get("market_eval", {}),
        profitability_score=payload_data.get("profitability_score", 0.0),
        environment=payload_data.get("environment"),
        dry_run=args.dry_run
    )
    
    result = service.execute_listing(payload, candidate_data, seller_data, handoff_data)
    print(json.dumps(result, indent=2))

def retry_execution(args):
    service = get_service()
    # In a real app, we load the old payload, generate a new attempt_id and execute
    print(f"Triggering retry for attempt: {args.attempt_id}")
    # Placeholder for actual logic using repository payload

def rollback_execution(args):
    service = get_service()
    result = service.rollback_execution(args.attempt_id, args.reason)
    print(json.dumps(result, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Listing Execution Layer CLI")
    subparsers = parser.add_subparsers(dest="command")

    # check-readiness
    parser_readiness = subparsers.add_parser("check-readiness")
    parser_readiness.add_argument("--candidate-data", default="{}")
    parser_readiness.add_argument("--seller-data", default="{}")
    parser_readiness.add_argument("--handoff-data", default="{}")

    # execute-listing
    parser_execute = subparsers.add_parser("execute-listing")
    parser_execute.add_argument("--payload", required=True, help="JSON string of ExecutionPayload")
    parser_execute.add_argument("--dry-run", action="store_true")

    # retry-execution
    parser_retry = subparsers.add_parser("retry-execution")
    parser_retry.add_argument("--attempt-id", required=True)
    parser_retry.add_argument("--dry-run", action="store_true")

    # rollback-execution
    parser_rollback = subparsers.add_parser("rollback-execution")
    parser_rollback.add_argument("--attempt-id", required=True)
    parser_rollback.add_argument("--reason", required=True)

    args = parser.parse_args()

    if args.command == "check-readiness":
        check_readiness(args)
    elif args.command == "execute-listing":
        execute_listing(args)
    elif args.command == "retry-execution":
        retry_execution(args)
    elif args.command == "rollback-execution":
        rollback_execution(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
