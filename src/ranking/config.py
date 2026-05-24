from pydantic_settings import BaseSettings
from pydantic import Field

class RankingSettings(BaseSettings):
    ranking_enabled: bool = Field(True, json_schema_extra={"env": "RANKING_ENABLED"})
    
    # Auto Launch Thresholds
    auto_launch_min_score: float = Field(70.0, json_schema_extra={"env": "RANKING_AUTO_LAUNCH_MIN_SCORE"})
    auto_launch_min_confidence: float = Field(0.75, json_schema_extra={"env": "RANKING_AUTO_LAUNCH_MIN_CONFIDENCE"})
    auto_launch_min_profit: float = Field(3000.0, json_schema_extra={"env": "RANKING_AUTO_LAUNCH_MIN_PROFIT"})
    auto_launch_min_margin: float = Field(0.18, json_schema_extra={"env": "RANKING_AUTO_LAUNCH_MIN_MARGIN"})
    auto_launch_min_roi: float = Field(0.20, json_schema_extra={"env": "RANKING_AUTO_LAUNCH_MIN_ROI"})
    
    # Capacity Limits
    max_auto_launch_per_run: int = Field(50, json_schema_extra={"env": "RANKING_MAX_AUTO_LAUNCH_PER_RUN"})
    max_auto_launch_per_seller: int = Field(10, json_schema_extra={"env": "RANKING_MAX_AUTO_LAUNCH_PER_SELLER"})
    defer_when_capacity_full: bool = Field(True, json_schema_extra={"env": "RANKING_DEFER_WHEN_CAPACITY_FULL"})
    
    # Staleness
    market_eval_stale_hours: int = Field(24, json_schema_extra={"env": "MARKET_EVAL_STALE_HOURS"})
    profitability_stale_hours: int = Field(24, json_schema_extra={"env": "PROFITABILITY_STALE_HOURS"})
    
    # Penalties & Others
    reject_market_confidence_threshold: float = Field(0.40, json_schema_extra={"env": "RANKING_REJECT_MARKET_CONFIDENCE_THRESHOLD"})
    capacity_penalty_enabled: bool = Field(True, json_schema_extra={"env": "RANKING_CAPACITY_PENALTY_ENABLED"})
    review_priority_strategy: str = Field("upside_risk_hybrid", json_schema_extra={"env": "RANKING_REVIEW_PRIORITY_STRATEGY"})

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"
