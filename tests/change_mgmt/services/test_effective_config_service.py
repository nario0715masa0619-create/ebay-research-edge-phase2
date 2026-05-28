import pytest
from src.change_mgmt.services.effective_config_service import EffectiveConfigService
from src.change_mgmt.services.config_version_service import ConfigVersionService
from src.change_mgmt.models.change_proposal import ChangeScopeType

@pytest.fixture
def config_service():
    return ConfigVersionService()

@pytest.fixture
def service(config_service):
    return EffectiveConfigService(config_service)

def test_compute_effective_config_empty(service):
    res = service.compute_effective_config("comp1")
    assert res.scope_type == ChangeScopeType.GLOBAL
    assert "empty defaults" in "\n".join(res.explanation_lines)

def test_compute_effective_config_global_only(service, config_service):
    v = config_service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {"k": "g"}, None, "u")
    config_service.activate_config_version(v.config_version_id)
    
    res = service.compute_effective_config("comp1")
    assert res.scope_type == ChangeScopeType.GLOBAL
    assert res.effective_config_snapshot["k"] == "g"

def test_compute_precedence(service, config_service):
    v1 = config_service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {"a": 1, "b": 1}, None, "u")
    config_service.activate_config_version(v1.config_version_id)
    
    v2 = config_service.create_config_version("comp1", ChangeScopeType.ENVIRONMENT, "prod", 1, {"b": 2, "c": 2}, None, "u")
    config_service.activate_config_version(v2.config_version_id)
    
    v3 = config_service.create_config_version("comp1", ChangeScopeType.SELLER, "s1", 1, {"c": 3}, None, "u")
    config_service.activate_config_version(v3.config_version_id)
    
    # Check seller override
    res = service.compute_effective_config("comp1", seller_account_id="s1", environment="prod")
    assert res.scope_type == ChangeScopeType.SELLER
    assert res.effective_config_snapshot["a"] == 1  # from global
    assert res.effective_config_snapshot["b"] == 2  # from env
    assert res.effective_config_snapshot["c"] == 3  # from seller

def test_explain_config(service, config_service):
    v1 = config_service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {"a": 1}, None, "u")
    config_service.activate_config_version(v1.config_version_id)
    
    exp = service.explain_effective_config("comp1", None, None)
    assert "GLOBAL" in exp

def test_list_effective_configs(service, config_service):
    v1 = config_service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {"a": 1}, None, "u")
    config_service.activate_config_version(v1.config_version_id)
    
    v2 = config_service.create_config_version("comp1", ChangeScopeType.ENVIRONMENT, "prod", 1, {"a": 2}, None, "u")
    config_service.activate_config_version(v2.config_version_id)
    
    v3 = config_service.create_config_version("comp2", ChangeScopeType.GLOBAL, None, 1, {"a": 1}, None, "u")
    config_service.activate_config_version(v3.config_version_id)
    
    configs = service.list_effective_configs_for_component("comp1")
    assert "global" in configs
    assert "env:prod" in configs
    assert "seller" not in configs
    assert len(configs) == 2
