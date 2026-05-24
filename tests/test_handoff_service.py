import pytest
from datetime import datetime
from src.ranking.models import DecisionClass, QueueType
from src.handoff.models import HandoffInput, HandoffStatus, HandoffDecision, HandoffResult
from src.handoff.config import HandoffSettings
from src.handoff.handoff_service import HandoffService

def get_base_input(candidate_id: str = "c_1", decision: DecisionClass = DecisionClass.AUTO_LAUNCH):
    return HandoffInput(
        ranking_decision_id="rdec_1",
        candidate_id=candidate_id,
        seller_account_id="s_1",
        environment="test",
        decision_class=decision,
        ranking_score=95.0,
        queue_type=QueueType.AUTO_LAUNCH_QUEUE,
        execution_blocked=False,
        recheck_required=False,
        stale_flag=False,
        has_valid_readiness_payload=True,
        operator_hold=False
    )

def test_handoff_success_mock():
    settings = HandoffSettings(use_mock_gateway=True)
    service = HandoffService(settings)
    
    input_data = get_base_input()
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[],
        run_handoff_count=0,
        seller_active_execution_count=0
    )
    
    assert result.handoff_status == HandoffStatus.COMPLETED
    assert result.handoff_decision == HandoffDecision.DISPATCH_NOW
    assert result.execution_allowed is True
    assert result.failure_reason == ""

def test_handoff_eligibility_failure():
    settings = HandoffSettings()
    service = HandoffService(settings)
    
    # Not auto launch
    input_data = get_base_input(decision=DecisionClass.MANUAL_REVIEW)
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[],
        run_handoff_count=0,
        seller_active_execution_count=0
    )
    
    assert result.handoff_status == HandoffStatus.REJECTED
    assert result.handoff_decision == HandoffDecision.REJECT_HANDOFF
    assert result.execution_allowed is False
    assert any("not auto_launch" in b for b in result.block_reasons)

def test_handoff_duplicate_suppression():
    settings = HandoffSettings()
    service = HandoffService(settings)
    
    input_data = get_base_input()
    
    # Simulate an existing completed handoff
    existing = HandoffResult(
        handoff_id="h_1",
        candidate_id=input_data.candidate_id,
        ranking_decision_id="rdec_0",
        seller_account_id="s_1",
        environment="test",
        handoff_status=HandoffStatus.COMPLETED,
        handoff_decision=HandoffDecision.DISPATCH_NOW
    )
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[existing],
        run_handoff_count=0,
        seller_active_execution_count=0
    )
    
    assert result.duplicate_suppressed is True
    assert result.handoff_status == HandoffStatus.REJECTED
    assert result.handoff_decision == HandoffDecision.REJECT_HANDOFF

def test_handoff_capacity_defer():
    settings = HandoffSettings(max_per_seller=5)
    service = HandoffService(settings)
    
    input_data = get_base_input()
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[],
        run_handoff_count=0,
        seller_active_execution_count=5 # Capacity full
    )
    
    assert result.deferred is True
    assert result.handoff_status == HandoffStatus.DEFERRED
    assert result.handoff_decision == HandoffDecision.DEFER
    assert any("limit" in b for b in result.block_reasons)

def test_handoff_mock_transient_retry():
    settings = HandoffSettings(use_mock_gateway=True)
    service = HandoffService(settings)
    
    # The mock gateway uses 'mock_transient_error' in candidate_id to simulate 503
    input_data = get_base_input("mock_transient_error")
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[],
        run_handoff_count=0,
        seller_active_execution_count=0
    )
    
    assert result.handoff_status == HandoffStatus.DEFERRED
    assert result.handoff_decision == HandoffDecision.RETRY_LATER
    assert result.retryable is True
    assert result.next_retry_at is not None
    assert "503" in result.failure_reason

def test_handoff_mock_fatal_error():
    settings = HandoffSettings(use_mock_gateway=True)
    service = HandoffService(settings)
    
    # The mock gateway uses 'mock_fatal_error' in candidate_id to simulate 400
    input_data = get_base_input("mock_fatal_error")
    
    result = service.process_handoff(
        input_data=input_data,
        existing_handoffs=[],
        run_handoff_count=0,
        seller_active_execution_count=0
    )
    
    assert result.handoff_status == HandoffStatus.REJECTED
    assert result.handoff_decision == HandoffDecision.REJECT_HANDOFF
    assert result.retryable is False
    assert "400" in result.failure_reason
