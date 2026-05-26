from typing import Optional, List, Tuple, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone

from src.learning.models.learning_record import (
    LearningRecord, RootCauseCategory, ImpactScope, 
    LearningRecordStatus, EffectivenessRating, ConfidenceLevel
)

class LearningRecordService:
    """Learning record 管理"""

    def __init__(self):
        self.records: Dict[UUID, LearningRecord] = {}

    def create_learning_record(
        self, 
        title: str, 
        summary: str, 
        category: RootCauseCategory, 
        scope: ImpactScope, 
        created_by: str, 
        linked_incident_id: Optional[UUID] = None
    ) -> LearningRecord:
        """新規 learning record 作成。status=OPEN。Returns: LearningRecord"""
        record = LearningRecord(
            learning_record_id=uuid4(),
            title=title,
            summary=summary,
            root_cause_category=category,
            root_cause_subcategory=None,
            impact_scope=scope,
            seller_account_id=None,
            environment=None,
            linked_incident_id=linked_incident_id,
            linked_policy_id=None,
            linked_report_id=None,
            is_false_positive=False,
            is_false_negative=False,
            is_near_miss=False,
            effectiveness_rating=EffectivenessRating.UNKNOWN,
            confidence_level=ConfidenceLevel.LOW,
            recommended_action_type=None,
            recommended_change_scope=None,
            status=LearningRecordStatus.OPEN,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            closed_at=None,
            metadata_json={}
        )
        self.records[record.learning_record_id] = record
        return record

    def get_learning_record_by_id(self, learning_record_id: UUID) -> Optional[LearningRecord]:
        """ID で取得。Returns: LearningRecord or None"""
        return self.records.get(learning_record_id)

    def list_learning_records(
        self, 
        status: Optional[LearningRecordStatus] = None, 
        category: Optional[RootCauseCategory] = None, 
        seller_account_id: Optional[str] = None, 
        environment: Optional[str] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[LearningRecord], int]:
        """フィルタ + ページネーション。Returns: ([records], total)"""
        filtered = list(self.records.values())
        
        if status:
            filtered = [r for r in filtered if r.status == status]
        if category:
            filtered = [r for r in filtered if r.root_cause_category == category]
        if seller_account_id:
            filtered = [r for r in filtered if r.seller_account_id == seller_account_id]
        if environment:
            filtered = [r for r in filtered if r.environment == environment]
            
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        total = len(filtered)
        return filtered[offset:offset+limit], total

    def update_learning_record(
        self, 
        learning_record_id: UUID, 
        title: Optional[str] = None, 
        summary: Optional[str] = None, 
        category: Optional[RootCauseCategory] = None, 
        effectiveness: Optional[EffectivenessRating] = None, 
        confidence: Optional[ConfidenceLevel] = None
    ) -> LearningRecord:
        """更新。Returns: 更新済み record"""
        record = self.records.get(learning_record_id)
        if not record:
            raise ValueError(f"LearningRecord {learning_record_id} not found")
            
        if title is not None:
            record.title = title
        if summary is not None:
            record.summary = summary
        if category is not None:
            record.root_cause_category = category
        if effectiveness is not None:
            record.effectiveness_rating = effectiveness
        if confidence is not None:
            record.confidence_level = confidence
            
        record.updated_at = datetime.utcnow()
        return record

    def close_learning_record(self, learning_record_id: UUID) -> LearningRecord:
        """status=CLOSED, closed_at=now。Returns: 更新済み record"""
        record = self.records.get(learning_record_id)
        if not record:
            raise ValueError(f"LearningRecord {learning_record_id} not found")
            
        record.status = LearningRecordStatus.CLOSED
        record.closed_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()
        return record

    def link_incident(self, learning_record_id: UUID, incident_id: UUID) -> LearningRecord:
        """incident リンク。Returns: 更新済み record"""
        record = self.records.get(learning_record_id)
        if not record:
            raise ValueError(f"LearningRecord {learning_record_id} not found")
            
        record.linked_incident_id = incident_id
        record.updated_at = datetime.utcnow()
        return record

    def link_policy(self, learning_record_id: UUID, policy_id: UUID) -> LearningRecord:
        """policy リンク。Returns: 更新済み record"""
        record = self.records.get(learning_record_id)
        if not record:
            raise ValueError(f"LearningRecord {learning_record_id} not found")
            
        record.linked_policy_id = policy_id
        record.updated_at = datetime.utcnow()
        return record

    def count_records_by_category(self) -> Dict[RootCauseCategory, int]:
        """category 別集計。Returns: {category: count}"""
        counts = {}
        for r in self.records.values():
            cat = r.root_cause_category
            counts[cat] = counts.get(cat, 0) + 1
        return counts
