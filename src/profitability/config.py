from pydantic_settings import BaseSettings
from pydantic import Field

class ProfitabilitySettings(BaseSettings):
    # Enable/Disable switch
    profitability_enabled: bool = Field(True, json_schema_extra={"env": "PROFITABILITY_ENABLED"})
    profitability_run_interval_seconds: int = Field(3600, json_schema_extra={"env": "PROFITABILITY_RUN_INTERVAL_SECONDS"})
    
    # Launch Thresholds
    min_launch_profit: float = Field(3000.0, json_schema_extra={"env": "PROFITABILITY_MIN_LAUNCH_PROFIT"})
    min_launch_margin: float = Field(0.18, json_schema_extra={"env": "PROFITABILITY_MIN_LAUNCH_MARGIN"})
    min_launch_roi: float = Field(0.20, json_schema_extra={"env": "PROFITABILITY_MIN_LAUNCH_ROI"})
    min_review_profit: float = Field(1500.0, json_schema_extra={"env": "PROFITABILITY_MIN_REVIEW_PROFIT"})
    reject_confidence_threshold: float = Field(0.40, json_schema_extra={"env": "PROFITABILITY_REJECT_CONFIDENCE_THRESHOLD"})
    
    # Conservative Defaults / Fallbacks
    default_marketplace_fee_rate: float = Field(0.15, json_schema_extra={"env": "PROFITABILITY_DEFAULT_MARKETPLACE_FEE_RATE"})
    default_fixed_marketplace_fee: float = Field(30.0, json_schema_extra={"env": "PROFITABILITY_DEFAULT_FIXED_MARKETPLACE_FEE"})
    default_payment_fee_rate: float = Field(0.04, json_schema_extra={"env": "PROFITABILITY_DEFAULT_PAYMENT_FEE_RATE"})
    default_fixed_payment_fee: float = Field(40.0, json_schema_extra={"env": "PROFITABILITY_DEFAULT_FIXED_PAYMENT_FEE"})
    
    default_packaging_cost: float = Field(200.0, json_schema_extra={"env": "PROFITABILITY_DEFAULT_PACKAGING_COST"})
    default_handling_cost: float = Field(300.0, json_schema_extra={"env": "PROFITABILITY_DEFAULT_HANDLING_COST"})
    default_outbound_shipping: float = Field(2000.0, json_schema_extra={"env": "PROFITABILITY_DEFAULT_OUTBOUND_SHIPPING"})
    
    # Penalty defaults
    default_low_comparable_penalty_rate: float = Field(0.05, json_schema_extra={"env": "PROFITABILITY_DEFAULT_LOW_COMPARABLE_PENALTY_RATE"})
    default_ambiguity_penalty_rate: float = Field(0.05, json_schema_extra={"env": "PROFITABILITY_DEFAULT_AMBIGUITY_PENALTY_RATE"})
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"
