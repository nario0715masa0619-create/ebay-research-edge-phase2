import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.escalation.models import EscalationState
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository
from src.escalation.ack_resolve_service import AckResolveService

@pytest.fixture
def state_repo_and_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    repo = PersistentEscalationStateRepository(session)
    service = AckResolveService(repo)
    
    yield session, repo, service
    
    session.close()
    engine.dispose()

def test_ack_resolve_service_lifecycle(state_repo_and_service):
    session, repo, service = state_repo_and_service

    # Create open state
    state = EscalationState(
        state_id="state_1",
        source_event_id="evt_1",
        source_history_id="hist_1",
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku="SKU-1",
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:SKU-1:logical_1",
        current_status="open",
        current_severity="error",
        current_priority="high"
    )
    repo.upsert_open_state(state)

    # 1. Acknowledge
    ok = service.acknowledge("state_1", actor_id="operator_1", note="Investigating")
    assert ok is True
    s = repo.get_by_state_id("state_1")
    assert s.current_status == "acknowledged"
    assert s.acked_by == "operator_1"
    assert s.acked_at is not None

    # 2. Silence
    until = datetime.now() + timedelta(hours=2)
    ok = service.silence("state_1", silenced_until=until, actor_id="operator_1", note="Wait for deployment")
    assert ok is True
    s = repo.get_by_state_id("state_1")
    assert s.current_status == "silenced"
    assert s.silenced_until is not None

    # 3. Unsilence
    ok = service.unsilence("state_1", actor_id="operator_1", note="Deployment done early")
    assert ok is True
    s = repo.get_by_state_id("state_1")
    assert s.current_status == "open"
    assert s.silenced_until is None

    # 4. Resolve
    ok = service.resolve("state_1", actor_id="operator_2", note="Fixed token refresh")
    assert ok is True
    s = repo.get_by_state_id("state_1")
    assert s.current_status == "resolved"
    assert s.resolved_by == "operator_2"
    assert s.resolved_at is not None
    assert s.resolution_note == "Fixed token refresh"

    # 5. Reopen
    ok = service.reopen("state_1", actor_id="operator_1", note="Re-occurred again")
    assert ok is True
    s = repo.get_by_state_id("state_1")
    assert s.current_status == "open"
    assert s.resolved_at is None
    assert s.resolved_by is None
    assert s.resolution_note is None
