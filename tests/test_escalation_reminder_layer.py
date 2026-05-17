import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.db.models import NotificationHistoryModel, JobRunModel
from src.escalation.models import (
    EscalationState,
    EscalationPolicy,
    EscalationStep
)
from src.escalation.event_normalizer import NormalizedEscalationEvent, EscalationEventNormalizer
from src.escalation.policies import DEFAULT_POLICIES
from src.repositories.persistent_escalation_state_repository import (
    PersistentEscalationStateRepository,
    PersistentEscalationPolicyRepository
)
from src.escalation.bootstrap import EscalationBootstrap
from src.escalation.runner import EscalationRunner

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

@pytest.fixture
def mock_notif_dispatcher():
    dispatcher = MagicMock()
    # Mock return value for notify method
    res = MagicMock()
    dispatch_res = MagicMock(success_flag=True, channel_name="slack")
    res.results = [dispatch_res]
    dispatcher.notify.return_value = res
    return dispatcher

def test_normalized_event_ingestion_and_dedupe(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]

    # Ingest event 1
    norm_event = NormalizedEscalationEvent(
        source_event_id="evt_1",
        source_history_id="hist_1",
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku="SKU-1",
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:SKU-1:logical_1",
        severity="error",
        priority="high",
        payload={"job_name": "test_job"}
    )

    runner._ingest_normalized_event(norm_event, dry_run=False)

    # Ingest duplicate event (should deduplicate / reuse same state row)
    runner._ingest_normalized_event(norm_event, dry_run=False)

    states = state_repo.list_recent()
    assert len(states) == 1
    assert states[0].dedupe_key == norm_event.dedupe_key

def test_reminder_evaluation_and_max_count(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]
    policy_repo = components["policy_repo"]

    # 1. Custom policy: max count = 2, interval = 300s
    policy = EscalationPolicy(
        policy_id="test_reminder_policy",
        name="Test Reminder Policy",
        enabled=True,
        seller_account_id="SELLER-X",
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
        state_id="state_r",
        source_event_id="evt_1",
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

    # First run: interval elapsed, reminder count is 0 -> should dispatch reminder
    res = runner.run(db_session, dry_run=False)
    assert res.reminder_sent_count == 1

    s1 = state_repo.get_by_state_id("state_r")
    assert s1.reminder_count == 1

    # Immediate second run: cooldown active -> should skip
    res2 = runner.run(db_session, dry_run=False)
    assert res2.reminder_sent_count == 0

    # Advance time: reminder_count is 1 -> should dispatch reminder 2
    state_repo.increment_reminder_count("state_r", 1, datetime.now() - timedelta(seconds=400))

    res3 = runner.run(db_session, dry_run=False)
    assert res3.reminder_sent_count == 1

    s2 = state_repo.get_by_state_id("state_r")
    assert s2.reminder_count == 2

    # Advance time: max reminder reached -> should skip further reminders
    state_repo.increment_reminder_count("state_r", 2, datetime.now() - timedelta(seconds=400))

    res4 = runner.run(db_session, dry_run=False)
    assert res4.reminder_sent_count == 0

def test_silence_respected(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]
    policy_repo = components["policy_repo"]

    policy = EscalationPolicy(
        policy_id="test_silence_policy",
        name="Test Silence Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="auth_refresh_failed",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=300,
        reminder_max_count=5,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False
    )
    policy_repo.upsert(policy)

    state = EscalationState(
        state_id="state_s",
        source_event_id="evt_1",
        source_history_id=None,
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku=None,
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:none:test",
        current_status="silenced",
        current_severity="error",
        current_priority="high",
        first_seen_at=datetime.now() - timedelta(seconds=600),
        last_seen_at=datetime.now() - timedelta(seconds=600),
        silenced_until=datetime.now() + timedelta(hours=1)
    )
    state_repo.upsert_open_state(state)

    # Silenced until +1 hour -> should skip reminder
    res = runner.run(db_session, dry_run=False)
    assert res.reminder_sent_count == 0

    # Expire silence
    state_repo.mark_silenced("state_s", datetime.now() - timedelta(seconds=1), "test_operator")

    # Silence expired -> should send reminder
    res2 = runner.run(db_session, dry_run=False)
    assert res2.reminder_sent_count == 1

def test_progressive_escalation_steps(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]
    policy_repo = components["policy_repo"]

    # Policy with 1 escalation step: 600s after first seen, min 1 repeat count
    policy = EscalationPolicy(
        policy_id="test_escalate_policy",
        name="Test Escalate Policy",
        enabled=True,
        seller_account_id="SELLER-X",
        environment_type=None,
        event_type="auth_refresh_failed",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=300,
        reminder_max_count=5,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True,
        escalation_steps=[
            EscalationStep(
                step_index=1,
                after_seconds=600,
                min_repeat_count=1,
                target_severity="critical",
                target_priority="critical",
                target_channels=["slack", "webhook"],
                cooldown_seconds=300,
                require_unacked=True
            )
        ]
    )
    policy_repo.upsert(policy)

    state = EscalationState(
        state_id="state_e",
        source_event_id="evt_1",
        source_history_id=None,
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku=None,
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:none:test",
        current_status="open",
        current_severity="error",
        current_priority="high",
        first_seen_at=datetime.now() - timedelta(seconds=700),
        last_seen_at=datetime.now() - timedelta(seconds=700),
        reminder_count=1
    )
    state_repo.upsert_open_state(state)

    # Should trigger escalation step 1
    res = runner.run(db_session, dry_run=False)
    assert res.escalation_sent_count == 1

    s = state_repo.get_by_state_id("state_e")
    assert s.escalation_level == 1
    assert s.current_status == "escalated"
    assert s.current_severity == "critical"

def test_dry_run_safety(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]

    # Ingest event under dry-run
    norm_event = NormalizedEscalationEvent(
        source_event_id="evt_dry",
        source_history_id=None,
        source_event_type="auth_refresh_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku=None,
        dedupe_key="auth_refresh_failed:SELLER-X:sandbox:none:dry",
        severity="error",
        priority="high",
        payload={}
    )
    runner._ingest_normalized_event(norm_event, dry_run=True)

    states = state_repo.list_recent()
    assert len(states) == 0  # Dry run prevents persistence

def test_auto_resolution_on_job_success(db_session, mock_notif_dispatcher):
    components = EscalationBootstrap.bootstrap(db_session, mock_notif_dispatcher)
    runner = components["runner"]
    state_repo = components["state_repo"]

    state = EscalationState(
        state_id="state_job",
        source_event_id="run_1",
        source_history_id=None,
        source_event_type="scheduled_job_failed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        sku=None,
        dedupe_key="scheduled_job_failed:SELLER-X:sandbox:none:monitoring",
        current_status="open",
        current_severity="error",
        current_priority="high",
        first_seen_at=datetime.now() - timedelta(seconds=600),
        last_seen_at=datetime.now() - timedelta(seconds=600)
    )
    state_repo.upsert_open_state(state)

    # Insert a successful completed job run after last_seen_at
    success_run = JobRunModel(
        run_id="run_2",
        job_name="monitoring",
        status="completed",
        seller_account_id="SELLER-X",
        environment_type="sandbox",
        started_at=datetime.now() - timedelta(seconds=100),
        finished_at=datetime.now() - timedelta(seconds=90)
    )
    db_session.add(success_run)
    db_session.commit()

    # Process auto resolution
    resolved = components["unresolved_selector"].process_auto_resolutions(db_session)
    assert resolved == 1

    s = state_repo.get_by_state_id("state_job")
    assert s.current_status == "resolved"
    assert s.resolved_by == "system_resolver"
