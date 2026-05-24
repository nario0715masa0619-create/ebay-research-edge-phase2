import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.admin_cli.services.handoff_ops_service import HandoffOpsService
from src.db.base import Base

# Assuming DB URL setup logic is imported or initialized somewhere
# For mock CLI usage, we assume a session is available
engine = create_engine('sqlite:///ebay_research.db')
SessionLocal = sessionmaker(bind=engine)

@click.group()
def handoff():
    """Handoff Management Commands."""
    pass

@handoff.command("run")
@click.argument("candidate_id")
@click.argument("seller_account_id")
@click.argument("environment")
def run_handoff_cmd(candidate_id: str, seller_account_id: str, environment: str):
    """Run handoff process for a candidate."""
    with SessionLocal() as session:
        ops = HandoffOpsService(session)
        res = ops.run_handoff(candidate_id, seller_account_id, environment)
        
        if res:
            click.echo(f"Handoff ID: {res.handoff_id}")
            click.echo(f"Status: {res.handoff_status.value}")
            click.echo(f"Decision: {res.handoff_decision.value}")
            if res.block_reasons:
                click.echo(f"Block Reasons: {', '.join(res.block_reasons)}")
            if res.failure_reason:
                click.echo(f"Failure Reason: {res.failure_reason}")
        else:
            click.echo("Handoff execution failed or candidate not found.")

@handoff.command("show")
@click.argument("handoff_id")
def show_handoff_cmd(handoff_id: str):
    """Show details of a specific handoff."""
    with SessionLocal() as session:
        ops = HandoffOpsService(session)
        res = ops.get_handoff_by_id(handoff_id)
        if res:
            click.echo(f"Handoff ID: {res.handoff_id}")
            click.echo(f"Candidate: {res.candidate_id}")
            click.echo(f"Status: {res.handoff_status.value}")
            click.echo(f"Decision: {res.handoff_decision.value}")
            click.echo(f"Execution Allowed: {res.execution_allowed}")
            click.echo(f"Next Retry: {res.next_retry_at}")
        else:
            click.echo("Handoff not found.")
