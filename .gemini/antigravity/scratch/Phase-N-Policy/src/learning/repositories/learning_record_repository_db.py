from typing import Optional, List, Tuple, Dict
from uuid import UUID
from datetime import datetime, timedelta
from src.learning.models.learning_record import LearningRecord, LearningRecordStatus, RootCauseCategory

class LearningRecordRepository:
    """DB-backed learning record repository"""
    def __init__(self):
        # Using a dict to mock DB for tests, real implementation would use sqlalchemy session
        self.records = {}

    def create_record(self, record: LearningRecord) -> LearningRecord:
        self.records[record.learning_record_id] = record
        return record

    def get_record_by_id(self, learning_record_id: UUID) -> Optional[LearningRecord]:
        return self.records.get(learning_record_id)

    def update_record(self, record: LearningRecord) -> LearningRecord:
        if record.learning_record_id in self.records:
            self.records[record.learning_record_id] = record
        return record

    def list_records(
        self, 
        status: Optional[LearningRecordStatus] = None, 
        category: Optional[RootCauseCategory] = None, 
        seller_account_id: Optional[str] = None, 
        environment: Optional[str] = None, 
        false_positive: Optional[bool] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[LearningRecord], int]:
        
        filtered = list(self.records.values())
        if status:
            filtered = [r for r in filtered if r.status == status]
        if category:
            filtered = [r for r in filtered if r.root_cause_category == category]
        if seller_account_id:
            filtered = [r for r in filtered if r.seller_account_id == seller_account_id]
        if environment:
            filtered = [r for r in filtered if r.environment == environment]
        if false_positive is not None:
            filtered = [r for r in filtered if r.is_false_positive == false_positive]
            
        total = len(filtered)
        # sort by created_at DESC
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[offset:offset+limit], total

    def get_records_by_category(self, category: RootCauseCategory) -> List[LearningRecord]:
        return [r for r in self.records.values() if r.root_cause_category == category]

    def get_records_by_seller(self, seller_account_id: str) -> List[LearningRecord]:
        return [r for r in self.records.values() if r.seller_account_id == seller_account_id]

    def get_records_by_environment(self, environment: str) -> List[LearningRecord]:
        return [r for r in self.records.values() if r.environment == environment]

    def count_records_by_status(self) -> Dict[LearningRecordStatus, int]:
        counts = {}
        for r in self.records.values():
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def count_records_by_category(self) -> Dict[RootCauseCategory, int]:
        counts = {}
        for r in self.records.values():
            counts[r.root_cause_category] = counts.get(r.root_cause_category, 0) + 1
        return counts

    def get_stale_records(self, days_old: int = 14) -> List[LearningRecord]:
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        return [
            r for r in self.records.values() 
            if r.status in [LearningRecordStatus.OPEN, LearningRecordStatus.UNDER_ANALYSIS] 
            and r.created_at < cutoff
        ]
