import os
from dataclasses import dataclass
from typing import Optional

class ConfigurationError(Exception):
    """Raised when there is an invalid configuration for the application."""
    pass

def _parse_bool(val: Optional[str], default: bool) -> bool:
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("true", "1", "yes", "on", "y")

def _parse_int(val: Optional[str], default: int) -> int:
    if val is None or val.strip() == "":
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default

def _parse_str(val: Optional[str], default: Optional[str] = None) -> Optional[str]:
    if val is None or val.strip() == "":
        return default
    return val.strip()

@dataclass
class MarketEvalSettings:
    market_data_provider: str = "mock"
    rapidapi_key: Optional[str] = None
    rapidapi_host: Optional[str] = None
    use_completed_data: bool = True
    provider_timeout_seconds: int = 20
    enable_fixture_mode: bool = True
    save_raw_provider_response: bool = False
    fail_on_provider_error: bool = False
    min_comparable_count: int = 3
    max_results: int = 50
    outlier_trim_enabled: bool = True
    app_env: str = "development"
    environment_type: str = "dev"

    @classmethod
    def from_env(cls) -> "MarketEvalSettings":
        return cls(
            market_data_provider=_parse_str(os.getenv("MARKET_DATA_PROVIDER"), "mock"),
            rapidapi_key=_parse_str(os.getenv("RAPIDAPI_KEY")),
            rapidapi_host=_parse_str(os.getenv("RAPIDAPI_HOST"), "ebay-average-selling-price.p.rapidapi.com"),
            use_completed_data=_parse_bool(os.getenv("MARKET_EVAL_USE_COMPLETED_DATA"), True),
            provider_timeout_seconds=_parse_int(os.getenv("MARKET_EVAL_PROVIDER_TIMEOUT_SECONDS"), 20),
            enable_fixture_mode=_parse_bool(os.getenv("MARKET_EVAL_ENABLE_FIXTURE_MODE"), True),
            save_raw_provider_response=_parse_bool(os.getenv("MARKET_EVAL_SAVE_RAW_PROVIDER_RESPONSE"), False),
            fail_on_provider_error=_parse_bool(os.getenv("MARKET_EVAL_FAIL_ON_PROVIDER_ERROR"), False),
            min_comparable_count=_parse_int(os.getenv("MARKET_EVAL_MIN_COMPARABLE_COUNT"), 3),
            max_results=_parse_int(os.getenv("MARKET_EVAL_MAX_RESULTS"), 50),
            outlier_trim_enabled=_parse_bool(os.getenv("MARKET_EVAL_OUTLIER_TRIM_ENABLED"), True),
            app_env=_parse_str(os.getenv("APP_ENV"), "development"),
            environment_type=_parse_str(os.getenv("ENVIRONMENT_TYPE"), "dev")
        )

    def validate_live_provider(self):
        """Validate settings required for the live RapidAPI provider."""
        if self.market_data_provider == "rapidapi_completed":
            if not self.rapidapi_key:
                raise ConfigurationError("MARKET_DATA_PROVIDER=rapidapi_completed but RAPIDAPI_KEY is missing")
            if not self.rapidapi_host:
                raise ConfigurationError("MARKET_DATA_PROVIDER=rapidapi_completed but RAPIDAPI_HOST is missing")
        elif self.market_data_provider != "mock":
            raise ConfigurationError(f"Unsupported MARKET_DATA_PROVIDER: {self.market_data_provider}")
