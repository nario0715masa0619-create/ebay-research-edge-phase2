import pytest
import os
from src.market_eval.config import MarketEvalSettings, ConfigurationError, _parse_bool, _parse_int

def test_parse_bool():
    assert _parse_bool("true", False) is True
    assert _parse_bool("1", False) is True
    assert _parse_bool("yes", False) is True
    assert _parse_bool("false", True) is False
    assert _parse_bool("", True) is True
    assert _parse_bool(None, False) is False

def test_parse_int():
    assert _parse_int("10", 5) == 10
    assert _parse_int("invalid", 5) == 5
    assert _parse_int("", 5) == 5
    assert _parse_int(None, 5) == 5

def test_default_settings():
    # Verify default instantiated settings without env variables match requirements
    settings = MarketEvalSettings()
    assert settings.market_data_provider == "mock"
    assert settings.enable_fixture_mode is True
    
    # Should validate without error
    settings.validate_live_provider()

def test_live_provider_validation_success():
    settings = MarketEvalSettings(
        market_data_provider="rapidapi_completed",
        rapidapi_key="secret",
        rapidapi_host="api.rapidapi.com"
    )
    # Should validate without error
    settings.validate_live_provider()

def test_live_provider_validation_missing_key():
    settings = MarketEvalSettings(
        market_data_provider="rapidapi_completed",
        rapidapi_key=None,
        rapidapi_host="api.rapidapi.com"
    )
    with pytest.raises(ConfigurationError, match="MARKET_DATA_PROVIDER=rapidapi_completed but RAPIDAPI_KEY is missing"):
        settings.validate_live_provider()

def test_live_provider_validation_missing_host():
    settings = MarketEvalSettings(
        market_data_provider="rapidapi_completed",
        rapidapi_key="secret",
        rapidapi_host=None
    )
    with pytest.raises(ConfigurationError, match="MARKET_DATA_PROVIDER=rapidapi_completed but RAPIDAPI_HOST is missing"):
        settings.validate_live_provider()

def test_unsupported_provider():
    settings = MarketEvalSettings(market_data_provider="unknown")
    with pytest.raises(ConfigurationError, match="Unsupported MARKET_DATA_PROVIDER: unknown"):
        settings.validate_live_provider()

def test_from_env_overrides(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "rapidapi_completed")
    monkeypatch.setenv("RAPIDAPI_KEY", "testkey")
    monkeypatch.setenv("MARKET_EVAL_MAX_RESULTS", "100")
    monkeypatch.setenv("MARKET_EVAL_ENABLE_FIXTURE_MODE", "false")
    
    settings = MarketEvalSettings.from_env()
    assert settings.market_data_provider == "rapidapi_completed"
    assert settings.rapidapi_key == "testkey"
    assert settings.max_results == 100
    assert settings.enable_fixture_mode is False
    
    settings.validate_live_provider()
