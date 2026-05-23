from typing import List, Optional
from sqlalchemy import select
from src.db.session import SessionManager
from src.db.models import AliasDictionaryModel
from dataclasses import dataclass

@dataclass
class AliasRecord:
    alias_id: str
    alias_type: str
    token: str
    resolution: str
    source_platform: Optional[str]
    enabled: bool

class PersistentAliasDictionaryRepository:
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()
        
    def get_all_enabled_aliases(self) -> List[AliasRecord]:
        with self.session_manager.session() as session:
            stmt = select(AliasDictionaryModel).where(AliasDictionaryModel.enabled == True)
            records = session.execute(stmt).scalars().all()
            
            return [
                AliasRecord(
                    alias_id=r.alias_id,
                    alias_type=r.alias_type,
                    token=r.token,
                    resolution=r.resolution,
                    source_platform=r.source_platform,
                    enabled=r.enabled
                )
                for r in records
            ]
            
    def save_alias(self, record: AliasRecord):
        with self.session_manager.session() as session:
            db_record = session.execute(
                select(AliasDictionaryModel).where(AliasDictionaryModel.alias_id == record.alias_id)
            ).scalar_one_or_none()
            
            if not db_record:
                db_record = AliasDictionaryModel(alias_id=record.alias_id)
                session.add(db_record)
                
            db_record.alias_type = record.alias_type
            db_record.token = record.token
            db_record.resolution = record.resolution
            db_record.source_platform = record.source_platform
            db_record.enabled = record.enabled
            
            session.commit()
            
    def disable_alias(self, alias_id: str):
        with self.session_manager.session() as session:
            db_record = session.execute(
                select(AliasDictionaryModel).where(AliasDictionaryModel.alias_id == alias_id)
            ).scalar_one_or_none()
            
            if db_record:
                db_record.enabled = False
                session.commit()
