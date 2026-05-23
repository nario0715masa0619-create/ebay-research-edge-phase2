import pytest
from src.discovery.variation_detector import VariationDetector
from src.discovery.bundle_detector import BundleDetector
from src.discovery.models import VariationDecisionClass, BundleDecisionClass
from src.discovery.review_flagger import ReviewFlagger
from src.discovery.models import MatchEvidence

def test_variation_capacity_mismatch():
    vd = VariationDetector()
    vars1 = vd.extract_variations("Sony PS5 825GB Console")
    vars2 = vd.extract_variations("Sony PS5 1TB Console")
    assert vars1.get("capacity") == "825GB"
    assert vars2.get("capacity") == "1TB"
    
    decision = vd.compare(vars1, vars2)
    assert decision.decision_class == VariationDecisionClass.CONFLICT
    assert decision.penalty_score == 1.0

def test_variation_color_mismatch():
    vd = VariationDetector()
    vars1 = vd.extract_variations("Nintendo Switch Lite Coral")
    vars2 = vd.extract_variations("Nintendo Switch Lite Blue")
    assert vars1.get("color") == "coral"
    assert vars2.get("color") == "blue"
    
    decision = vd.compare(vars1, vars2)
    assert decision.decision_class == VariationDecisionClass.AMBIGUOUS
    assert decision.penalty_score == 0.4

def test_bundle_single_vs_set():
    bd = BundleDetector()
    flags1 = bd.extract_flags("Pokemon Game")
    flags2 = bd.extract_flags("Pokemon Game 2点セット")
    assert "set" not in flags1
    assert "set" in flags2
    
    decision = bd.compare(flags1, flags2)
    assert decision.decision_class == BundleDecisionClass.CONFLICT
    assert decision.penalty_score == 1.0
    
def test_bundle_accessories_difference():
    bd = BundleDetector()
    flags1 = bd.extract_flags("Camera Body")
    flags2 = bd.extract_flags("Camera Body おまけ付き")
    assert "with_accessories" not in flags1
    assert "with_accessories" in flags2
    
    decision = bd.compare(flags1, flags2)
    assert decision.decision_class == BundleDecisionClass.CONFLICT
    assert decision.penalty_score == 0.5 # Handled as conflict but soft penalty inside bundle_detector logic (Wait, I put penalty=0.5, and review_flagger checks >= 0.5)

def test_review_flagger_activation():
    flagger = ReviewFlagger()
    ev = MatchEvidence(evidence_id="ev_1", normalized_item_id="n_1", candidate_id="c_1")
    
    # Base case with identifiers
    ev.identifier_hits["gtin"] = True
    assert flagger.evaluate(ev) == False
    
    # Variation ambiguity activates review
    ev.variation_penalty = 0.4
    assert flagger.evaluate(ev) == True
    
    # Bundle ambiguity activates review
    ev.variation_penalty = 0.0
    ev.bundle_penalty = 0.5
    assert flagger.evaluate(ev) == True
    
    # Missing strict ID activates review
    ev.bundle_penalty = 0.0
    ev.identifier_hits["gtin"] = False
    ev.brand_match_score = 0.0
    assert flagger.evaluate(ev) == True
