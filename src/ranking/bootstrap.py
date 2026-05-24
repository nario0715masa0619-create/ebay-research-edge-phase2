from src.ranking.config import RankingSettings
from src.ranking.scoring_service import RankingScoringService
from src.repositories.persistent_ranking_decision_repository import PersistentRankingDecisionRepository
from src.db.session import SessionLocal

class RankingBootstrap:
    _settings = None

    @classmethod
    def get_settings(cls) -> RankingSettings:
        if cls._settings is None:
            cls._settings = RankingSettings()
        return cls._settings

    @classmethod
    def get_scoring_service(cls) -> RankingScoringService:
        return RankingScoringService(settings=cls.get_settings())
        
    @classmethod
    def get_repository(cls) -> PersistentRankingDecisionRepository:
        db = SessionLocal()
        return PersistentRankingDecisionRepository(db)
