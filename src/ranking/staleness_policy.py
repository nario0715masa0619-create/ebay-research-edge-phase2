from datetime import datetime, timezone
from src.ranking.models import RankingInput
from src.ranking.config import RankingSettings

class StalenessPolicy:
    def __init__(self, settings: RankingSettings):
        self.settings = settings
        
    def is_market_stale(self, input_data: RankingInput, now: datetime) -> bool:
        if not input_data.market_created_at:
            return True
        # timezone naive to aware mapping to ensure safe math
        m_time = input_data.market_created_at.replace(tzinfo=timezone.utc) if input_data.market_created_at.tzinfo is None else input_data.market_created_at
        n_time = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
        
        diff_hours = (n_time - m_time).total_seconds() / 3600.0
        return diff_hours > self.settings.market_eval_stale_hours

    def is_profitability_stale(self, input_data: RankingInput, now: datetime) -> bool:
        if not input_data.profitability_created_at:
            return True
        p_time = input_data.profitability_created_at.replace(tzinfo=timezone.utc) if input_data.profitability_created_at.tzinfo is None else input_data.profitability_created_at
        n_time = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
        
        diff_hours = (n_time - p_time).total_seconds() / 3600.0
        return diff_hours > self.settings.profitability_stale_hours
        
    def evaluate_staleness(self, input_data: RankingInput, now: datetime = None) -> bool:
        if now is None:
            now = datetime.utcnow()
            
        return self.is_market_stale(input_data, now) or self.is_profitability_stale(input_data, now)
