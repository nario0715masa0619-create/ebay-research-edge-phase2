import pytest
from src.learning.services.false_signal_analysis_service import FalseSignalAnalysisService

@pytest.fixture
def service():
    return FalseSignalAnalysisService()

def test_identify_false_positives(service):
    res = service.identify_false_positives()
    assert len(res) > 0

def test_identify_false_negatives(service):
    res = service.identify_false_negatives()
    assert len(res) > 0

def test_calculate_false_positive_rate(service):
    noisy = service.calculate_false_positive_rate("noisy")
    all_rate = service.calculate_false_positive_rate("all")
    assert noisy > all_rate

def test_calculate_false_negative_rate(service):
    res = service.calculate_false_negative_rate()
    assert res > 0

def test_analyze_false_signal_pattern(service):
    res = service.analyze_false_signal_pattern("pattern")
    assert "fp_count" in res

def test_recommend_detection_threshold_adjustment(service):
    res = service.recommend_detection_threshold_adjustment("noisy")
    assert res is not None
    assert "adjustment" in res
    
    perfect = service.recommend_detection_threshold_adjustment("perfect")
    assert perfect is None

def test_identify_near_miss_events(service):
    res = service.identify_near_miss_events()
    assert len(res) > 0
