import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.escalation.models import EscalationPolicy, EscalationState
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository, PersistentEscalationPolicyRepository
from src.orchestrator.bootstrap import OrchestratorBootstrap
from src.orchestrator.manual_trigger import ManualTrigger

class MockNotificationDispatcher:
    def __init__(self):
        self.sent_notifications = []

    def notify(self, event, dry_run=False):
        self.sent_notifications.append((event, dry_run))

@pytest.fixture
def db_session():
    # In-memory SQLite for orchestrator testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_escalation_reminder_job_orchestration(db_session):
    # 1. Setup mock notification dispatcher
    mock_dispatcher = MockNotificationDispatcher()

    # 2. Setup mock containers passed to OrchestratorBootstrap
    repositories = {}
    pipelines = {}
    gateways = {}

    # 3. Bootstrap Orchestrator
    orchestrator = OrchestratorBootstrap.bootstrap(
        repositories=repositories,
        pipelines=pipelines,
        gateways=gateways,
        notification_dispatcher=mock_dispatcher
    )

    # Verify registration
    job_def = orchestrator.engine.registry.get_job("escalation_reminder_job")
    assert job_def is not None
    assert job_def.interval_seconds == 300
    assert job_def.target_runner_name == "escalation_reminder_runner"

    # 4. Seed an unresolved state and policy via database session to verify integration
    state_repo = PersistentEscalationStateRepository(db_session)
    policy_repo = PersistentEscalationPolicyRepository(db_session)

    policy = EscalationPolicy(
        policy_id="orch_policy",
        name="Orchestrator Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="auth_refresh_failed",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=300,
        reminder_max_count=2,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False
    )
    policy_repo.upsert(policy)

    state = EscalationState(
        state_id="state_orch",
        source_event_id="evt_orch",
        source_history_id=None,
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku=None,
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:none:test",
        current_status="open",
        current_severity="error",
        current_priority="high",
        first_seen_at=datetime.now() - timedelta(seconds=600),
        last_seen_at=datetime.now() - timedelta(seconds=600),
        reminder_count=0
    )
    state_repo.upsert_open_state(state)

    # 5. Run standard engine cycle forcing only the escalation job
    # We patch/mock SessionManager inside EscalationReminderRunnerAdapter to yield our test db_session
    from src.db.session import SessionManager
    class TestSessionManager(SessionManager):
        def __init__(self, session):
            self.test_session = session
        
        def session(self):
            # context manager yielding our test session without closing it immediately
            class TestContext:
                def __init__(self, s): self.s = s
                def __enter__(self): return self.s
                def __exit__(self, exc_type, exc_val, exc_tb): pass
            return TestContext(self.test_session)
        
        def get_session(self):
            return self.test_session

    from src.escalation.runner_adapter import EscalationReminderRunnerAdapter
    adapter = EscalationReminderRunnerAdapter(session_manager=TestSessionManager(db_session))
    orchestrator.engine.runner_map["escalation_reminder_runner"] = adapter

    # Trigger via ManualTrigger
    trigger = ManualTrigger(orchestrator)
    results = trigger.trigger("escalation_reminder_job", dry_run=False)

    assert len(results) == 1
    job_result = results[0]
    assert job_result.status == "completed"
    assert job_result.success_flag is True

    # 6. Verify that it actually found and reminded the event!
    updated_state = state_repo.get_by_state_id("state_orch")
    assert updated_state.reminder_count == 1
    assert updated_state.last_reminded_at is not None
