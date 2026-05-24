from .config import MarketEvalSettings, ConfigurationError
from .market_search_gateway import MarketSearchGateway
from .mock_market_search_gateway import MockMarketSearchGateway
from .rapidapi_completed_items_gateway import RapidApiCompletedItemsGateway

class MarketEvalBootstrap:
    """
    Dependency Injection container for the Market Evaluation Layer.
    Initializes settings and selects the appropriate provider based on the MARKET_DATA_PROVIDER setting.
    """
    _gateway: MarketSearchGateway = None
    _settings: MarketEvalSettings = None
    
    @classmethod
    def get_settings(cls) -> MarketEvalSettings:
        if cls._settings is None:
            cls._settings = MarketEvalSettings.from_env()
        return cls._settings

    @classmethod
    def get_gateway(cls) -> MarketSearchGateway:
        if cls._gateway is None:
            settings = cls.get_settings()
            
            if settings.market_data_provider == "mock":
                cls._gateway = MockMarketSearchGateway(settings)
            elif settings.market_data_provider == "rapidapi_completed":
                settings.validate_live_provider()
                cls._gateway = RapidApiCompletedItemsGateway(settings)
            else:
                raise ConfigurationError(f"Unsupported MARKET_DATA_PROVIDER: {settings.market_data_provider}")
                
        return cls._gateway

    @classmethod
    def reset(cls):
        """For testing purposes."""
        cls._gateway = None
        cls._settings = None
