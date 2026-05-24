import pytest
from datetime import datetime, timezone, timedelta
from src.ranking.config import RankingSettings
from src.ranking.models import RankingInput, DecisionClass, QueueType, LaunchPriorityBucket
from src.ranking.scoring_service import RankingScoringService

def test_ranking_auto_launch_success():
    settings = RankingSettings()
    service = RankingScoringService(settings)
    
    # 理想的な高利益・高Confidence、リスクなしの候補
    input_data = RankingInput(
        candidate_id="c_1",
        seller_account_id="s_1",
        environment="test",
        market_evaluation_status="success",
        market_confidence=0.90,
        comparable_count=10,
        profitability_scoring_status="success",
        expected_net_profit=5000.0,
        expected_margin=0.25,
        expected_roi=0.30,
        confidence_adjusted_profit=4500.0,
        profitability_score=85.0,
        profitability_decision_status="launch_now",
        market_created_at=datetime.utcnow(),
        profitability_created_at=datetime.utcnow()
    )
    
    result = service.evaluate(input_data)
    
    assert result.decision_class == DecisionClass.AUTO_LAUNCH
    assert result.queue_type == QueueType.AUTO_LAUNCH_QUEUE
    assert result.execution_blocked is False
    assert result.recheck_required is False
    assert result.launch_priority_bucket is not None
    assert result.ranking_score > 50.0

def test_ranking_stale_data_blocks_auto_launch():
    settings = RankingSettings()
    service = RankingScoringService(settings)
    
    # 48時間前の古いデータ
    old_time = datetime.utcnow() - timedelta(hours=48)
    
    input_data = RankingInput(
        candidate_id="c_2",
        seller_account_id="s_1",
        environment="test",
        market_evaluation_status="success",
        market_confidence=0.90,
        profitability_scoring_status="success",
        expected_net_profit=5000.0,
        expected_margin=0.25,
        expected_roi=0.30,
        confidence_adjusted_profit=4500.0,
        profitability_decision_status="launch_now",
        market_created_at=old_time,
        profitability_created_at=old_time
    )
    
    result = service.evaluate(input_data)
    
    # Stale なら Auto Launch は絶対に防がれ、Review等に回る
    assert result.decision_class != DecisionClass.AUTO_LAUNCH
    assert result.recheck_required is True
    assert any("Stale data" in line for line in result.explanation_lines)
    
def test_ranking_reject_invalid_input():
    settings = RankingSettings()
    service = RankingScoringService(settings)
    
    input_data = RankingInput(
        candidate_id="c_3",
        seller_account_id="s_1",
        environment="test",
        profitability_scoring_status="input_incomplete"
    )
    
    result = service.evaluate(input_data)
    
    assert result.decision_class == DecisionClass.REJECT
    assert result.queue_type == QueueType.REJECT_ARCHIVE
    assert result.execution_blocked is True
    assert any("incomplete" in r for r in result.block_reasons)

def test_ranking_capacity_full_defers_to_watchlist():
    settings = RankingSettings()
    service = RankingScoringService(settings)
    
    # 良い候補だがセラーのキャパがフルの場合
    input_data = RankingInput(
        candidate_id="c_4",
        seller_account_id="s_1",
        environment="test",
        market_evaluation_status="success",
        market_confidence=0.90,
        profitability_scoring_status="success",
        expected_net_profit=5000.0,
        expected_margin=0.25,
        expected_roi=0.30,
        confidence_adjusted_profit=4500.0,
        profitability_decision_status="launch_now",
        seller_capacity_full=True,
        market_created_at=datetime.utcnow(),
        profitability_created_at=datetime.utcnow()
    )
    
    result = service.evaluate(input_data)
    
    # Deferred or Watchlist
    assert result.decision_class != DecisionClass.AUTO_LAUNCH
    assert result.execution_blocked is True
    assert result.queue_type == QueueType.WATCH_QUEUE
    assert result.launch_priority_bucket == LaunchPriorityBucket.DEFERRED
