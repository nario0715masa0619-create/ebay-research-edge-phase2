import pytest
from uuid import uuid4
from src.change_mgmt.services.config_version_service import ConfigVersionService
from src.change_mgmt.models.change_proposal import ChangeScopeType

@pytest.fixture
def service():
    return ConfigVersionService()

def test_create_version(service):
    v = service.create_config_version(
        "comp1", ChangeScopeType.GLOBAL, None, 1, {"k": "v"}, uuid4(), "user"
    )
    assert v.component_name == "comp1"
    assert v.is_active is False
    assert service.get_config_version_by_id(v.config_version_id) == v

def test_get_by_id_not_found(service):
    assert service.get_config_version_by_id(uuid4()) is None

def test_list_versions(service):
    service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {}, None, "u")
    service.create_config_version("comp2", ChangeScopeType.ENVIRONMENT, "prod", 1, {}, None, "u")
    
    vs, total = service.list_config_versions(component_name="comp1")
    assert total == 1
    
    vs, total = service.list_config_versions(scope_type=ChangeScopeType.ENVIRONMENT)
    assert total == 1
    assert vs[0].scope_target_id == "prod"

def test_activate_version(service):
    v = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {}, None, "u")
    res = service.activate_config_version(v.config_version_id)
    assert res.is_active is True
    assert res.effective_from is not None

def test_supersede_version(service):
    v1 = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {}, None, "u")
    service.activate_config_version(v1.config_version_id)
    
    v2 = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 2, {}, None, "u")
    res = service.supersede_config_version(v1.config_version_id, v2.config_version_id)
    
    assert res.is_active is True
    assert res.supersedes_config_version_id == v1.config_version_id
    assert v1.is_active is False
    assert v1.effective_until is not None

def test_expire_version(service):
    v1 = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {}, None, "u")
    service.activate_config_version(v1.config_version_id)
    
    res = service.expire_config_version(v1.config_version_id)
    assert res.is_active is False
    assert res.effective_until is not None

def test_get_active_for_scope(service):
    v1 = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 1, {}, None, "u")
    service.activate_config_version(v1.config_version_id)
    
    v2 = service.create_config_version("comp1", ChangeScopeType.GLOBAL, None, 2, {}, None, "u")
    # Not active yet
    
    res = service.get_active_version_for_scope("comp1", ChangeScopeType.GLOBAL, None)
    assert res == v1
    
    service.supersede_config_version(v1.config_version_id, v2.config_version_id)
    res = service.get_active_version_for_scope("comp1", ChangeScopeType.GLOBAL, None)
    assert res == v2
