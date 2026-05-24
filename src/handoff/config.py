from pydantic_settings import BaseSettings
from pydantic import Field

class HandoffSettings(BaseSettings):
    handoff_enabled: bool = Field(True, json_schema_extra={"env": "HANDOFF_ENABLED"})
    use_mock_gateway: bool = Field(True, json_schema_extra={"env": "HANDOFF_USE_MOCK_GATEWAY"})
    
    # Duplicate Suppression
    duplicate_suppression_window_seconds: int = Field(86400, json_schema_extra={"env": "HANDOFF_DUPLICATE_SUPPRESSION_WINDOW_SECONDS"}) # Default 24h
    
    # Capacity Limits
    max_per_run: int = Field(50, json_schema_extra={"env": "HANDOFF_MAX_PER_RUN"})
    max_per_seller: int = Field(10, json_schema_extra={"env": "HANDOFF_MAX_PER_SELLER"})
    defer_when_capacity_full: bool = Field(True, json_schema_extra={"env": "HANDOFF_DEFER_WHEN_CAPACITY_FULL"})
    
    # Cooldown
    seller_cooldown_seconds: int = Field(3600, json_schema_extra={"env": "HANDOFF_SELLER_COOLDOWN_SECONDS"})
    
    # Retry Policy
    retry_max_attempts: int = Field(3, json_schema_extra={"env": "HANDOFF_RETRY_MAX_ATTEMPTS"})
    retry_backoff_seconds: int = Field(600, json_schema_extra={"env": "HANDOFF_RETRY_BACKOFF_SECONDS"})
    escalate_after_failure_count: int = Field(3, json_schema_extra={"env": "HANDOFF_ESCALATE_AFTER_FAILURE_COUNT"})
    
    # Guards
    stale_reject_enabled: bool = Field(True, json_schema_extra={"env": "HANDOFF_STALE_REJECT_ENABLED"})

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"
