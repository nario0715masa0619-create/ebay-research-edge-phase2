import os
from src.profitability.config import ProfitabilitySettings
from src.profitability.scoring_service import ProfitabilityScoringService
from src.repositories.persistent_profitability_score_repository import PersistentProfitabilityScoreRepository
from src.db.session import SessionLocal

class ProfitabilityBootstrap:
    _settings = None

    @classmethod
    def get_settings(cls) -> ProfitabilitySettings:
        if cls._settings is None:
            cls._settings = ProfitabilitySettings()
        return cls._settings

    @classmethod
    def get_scoring_service(cls) -> ProfitabilityScoringService:
        return ProfitabilityScoringService(settings=cls.get_settings())
        
    @classmethod
    def get_repository(cls) -> PersistentProfitabilityScoreRepository:
        db = SessionLocal() # Usually this should be managed by caller context, but for simple scripts it's fine.
        return PersistentProfitabilityScoreRepository(db)
