from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from src.change_mgmt.models.config_version import ConfigVersion
from src.change_mgmt.models.change_proposal import ChangeScopeType
from src.change_mgmt.models.effective_config_decision import EffectiveConfigDecision
from src.change_mgmt.services.config_version_service import ConfigVersionService

class EffectiveConfigService:
    """Effective config 計算"""
    
    def __init__(self, config_version_service: ConfigVersionService = None):
        self.config_service = config_version_service or ConfigVersionService()

    def compute_effective_config(
        self, component_name: str, seller_account_id: Optional[str] = None, 
        environment: Optional[str] = None
    ) -> EffectiveConfigDecision:
        
        global_config = self.config_service.get_active_version_for_scope(
            component_name, ChangeScopeType.GLOBAL, None
        )
        env_config = None
        if environment:
            env_config = self.config_service.get_active_version_for_scope(
                component_name, ChangeScopeType.ENVIRONMENT, environment
            )
        seller_config = None
        if seller_account_id:
            seller_config = self.config_service.get_active_version_for_scope(
                component_name, ChangeScopeType.SELLER, seller_account_id
            )
            
        return self.compute_effective_config_with_precedence(
            component_name, global_config, env_config, seller_config
        )

    def compute_effective_config_with_precedence(
        self, component_name: str, global_config: Optional[ConfigVersion], 
        env_config: Optional[ConfigVersion], seller_config: Optional[ConfigVersion]
    ) -> EffectiveConfigDecision:
        
        effective_snapshot = {}
        explanation = []
        scope_type = ChangeScopeType.GLOBAL
        target_id = None
        version_id = None
        
        if global_config:
            effective_snapshot.update(global_config.config_snapshot)
            explanation.append("Applied GLOBAL config.")
            version_id = global_config.config_version_id
            
        if env_config:
            effective_snapshot.update(env_config.config_snapshot)
            explanation.append(f"Overridden by ENVIRONMENT config (env: {env_config.scope_target_id}).")
            scope_type = ChangeScopeType.ENVIRONMENT
            target_id = env_config.scope_target_id
            version_id = env_config.config_version_id
            
        if seller_config:
            effective_snapshot.update(seller_config.config_snapshot)
            explanation.append(f"Overridden by SELLER config (seller: {seller_config.scope_target_id}).")
            scope_type = ChangeScopeType.SELLER
            target_id = seller_config.scope_target_id
            version_id = seller_config.config_version_id
            
        if not version_id:
            # Fallback if no config exists at all
            explanation.append("No active configuration found. Using empty defaults.")
            from uuid import uuid4
            version_id = uuid4()  # Dummy ID for empty config

        return EffectiveConfigDecision(
            component_name=component_name,
            scope_type=scope_type,
            scope_target_id=target_id,
            effective_config_snapshot=effective_snapshot,
            effective_config_version_id=version_id,
            explanation_lines=explanation,
            evaluated_at=datetime.utcnow(),
            has_pending_changes=False,
            next_scheduled_change_id=None
        )

    def explain_effective_config(
        self, component_name: str, seller_account_id: Optional[str], environment: Optional[str]
    ) -> str:
        decision = self.compute_effective_config(component_name, seller_account_id, environment)
        return "\n".join(decision.explanation_lines)

    def list_effective_configs_for_component(self, component_name: str) -> Dict[str, EffectiveConfigDecision]:
        # Fetch all active configs for this component
        all_active = [v for v in self.config_service.versions.values() 
                     if v.component_name == component_name and v.is_active]
        
        results = {}
        # Simple implementation: just list the decisions for each defined target
        for v in all_active:
            if v.scope_type == ChangeScopeType.GLOBAL:
                results["global"] = self.compute_effective_config(component_name)
            elif v.scope_type == ChangeScopeType.ENVIRONMENT:
                results[f"env:{v.scope_target_id}"] = self.compute_effective_config(component_name, environment=v.scope_target_id)
            elif v.scope_type == ChangeScopeType.SELLER:
                results[f"seller:{v.scope_target_id}"] = self.compute_effective_config(component_name, seller_account_id=v.scope_target_id)
                
        return results
