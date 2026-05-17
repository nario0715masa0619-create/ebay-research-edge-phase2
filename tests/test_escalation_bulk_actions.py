import pytest
from datetime import datetime, timedelta
from typing import Optional

from src.escalation.bulk_action_service import BulkActionService

class MockStateRepository:
    def mark_acknowledged(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        return state_id != "fail_id"
        
    def mark_resolved(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        return state_id != "fail_id"
        
    def mark_silenced(self, state_id: str, silenced_until: datetime, actor_id: str, note: Optional[str] = None) -> bool:
        return state_id != "fail_id"
        
    def reopen_state(self, state_id: str, actor_id: str, note: Optional[str] = None) -> bool:
        return state_id != "fail_id"

@pytest.fixture
def bulk_service():
    repo = MockStateRepository()
    return BulkActionService(repo)

def test_bulk_ack_success_and_failure(bulk_service):
    state_ids = ["ok_1", "fail_id", "ok_2"]
    res = bulk_service.bulk_ack(state_ids, "actor")
    assert res["success_count"] == 2
    assert "fail_id" in res["failed_ids"]

def test_bulk_resolve_success_and_failure(bulk_service):
    state_ids = ["ok_1", "fail_id"]
    res = bulk_service.bulk_resolve(state_ids, "actor")
    assert res["success_count"] == 1
    assert "fail_id" in res["failed_ids"]

def test_bulk_silence_success_and_failure(bulk_service):
    state_ids = ["ok_1", "fail_id"]
    until = datetime.now() + timedelta(hours=24)
    res = bulk_service.bulk_silence(state_ids, until, "actor")
    assert res["success_count"] == 1
    assert "fail_id" in res["failed_ids"]

def test_bulk_reopen_success_and_failure(bulk_service):
    state_ids = ["ok_1", "fail_id"]
    res = bulk_service.bulk_reopen(state_ids, "actor")
    assert res["success_count"] == 1
    assert "fail_id" in res["failed_ids"]
