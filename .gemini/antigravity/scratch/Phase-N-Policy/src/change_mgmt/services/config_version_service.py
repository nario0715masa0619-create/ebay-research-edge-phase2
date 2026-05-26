from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from src.change_mgmt.models.config_version import ConfigVersion
from src.change_mgmt.models.change_proposal import ChangeScopeType

class ConfigVersionService:
    """Config version 管理"""
    
    def __init__(self):
        self.versions: Dict[UUID, ConfigVersion] = {}

    def create_config_version(
        self, component_name: str, scope_type: ChangeScopeType, 
        scope_target_id: Optional[str], version_number: int, 
        config_snapshot: Dict[str, Any], change_proposal_id: Optional[UUID], 
        created_by: str
    ) -> ConfigVersion:
        
        version = ConfigVersion(
            config_version_id=uuid4(),
            component_name=component_name,
            scope_type=scope_type,
            scope_target_id=scope_target_id,
            version_number=version_number,
            config_snapshot=config_snapshot,
            derived_from_change_proposal_id=change_proposal_id,
            effective_from=datetime.utcnow(),
            effective_until=None,
            is_active=False,
            supersedes_config_version_id=None,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.versions[version.config_version_id] = version
        return version

    def get_config_version_by_id(self, config_version_id: UUID) -> Optional[ConfigVersion]:
        return self.versions.get(config_version_id)

    def list_config_versions(
        self, component_name: Optional[str] = None, 
        scope_type: Optional[ChangeScopeType] = None, 
        scope_target_id: Optional[str] = None, 
        is_active: bool = False, limit: int = 100
    ) -> Tuple[List[ConfigVersion], int]:
        
        filtered = list(self.versions.values())
        if component_name:
            filtered = [v for v in filtered if v.component_name == component_name]
        if scope_type:
            filtered = [v for v in filtered if v.scope_type == scope_type]
        if scope_target_id:
            filtered = [v for v in filtered if v.scope_target_id == scope_target_id]
        if is_active:
            filtered = [v for v in filtered if v.is_active]
            
        total = len(filtered)
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[:limit], total

    def activate_config_version(self, config_version_id: UUID) -> ConfigVersion:
        version = self.versions[config_version_id]
        version.is_active = True
        version.effective_from = datetime.utcnow()
        return version

    def supersede_config_version(self, old_config_version_id: UUID, new_config_version_id: UUID) -> ConfigVersion:
        old_version = self.versions[old_config_version_id]
        new_version = self.versions[new_config_version_id]
        
        old_version.effective_until = datetime.utcnow()
        old_version.is_active = False
        
        new_version.supersedes_config_version_id = old_config_version_id
        new_version.is_active = True
        new_version.effective_from = datetime.utcnow()
        
        return new_version

    def expire_config_version(self, config_version_id: UUID) -> ConfigVersion:
        version = self.versions[config_version_id]
        version.effective_until = datetime.utcnow()
        version.is_active = False
        return version

    def get_active_version_for_scope(
        self, component_name: str, scope_type: ChangeScopeType, 
        scope_target_id: Optional[str]
    ) -> Optional[ConfigVersion]:
        
        active_versions = [
            v for v in self.versions.values() 
            if v.component_name == component_name 
            and v.scope_type == scope_type 
            and v.scope_target_id == scope_target_id 
            and v.is_active
        ]
        
        if not active_versions:
            return None
        # Return the most recently created one if multiple active
        active_versions.sort(key=lambda x: x.created_at, reverse=True)
        return active_versions[0]
