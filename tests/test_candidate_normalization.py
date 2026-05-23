import pytest
from src.discovery.models import RawSourceItem, CanonicalProductCandidate
from src.discovery.title_normalizer import TitleNormalizer
from src.discovery.identifier_normalizer import IdentifierNormalizer
from src.discovery.match_confidence import MatchConfidenceEngine
from src.discovery.entity_matcher import EntityMatcher
from src.discovery.candidate_normalizer import CandidateNormalizer

class MockCandidateRepo:
    def __init__(self):
        self.candidates = []
        
    def find_by_brand_mpn(self, brand, mpn):
        for c in self.candidates:
            # simple mock match
            if c.canonical_brand == brand and c.canonical_mpn.replace("-","") == mpn.replace("-",""):
                return c
        return None
        
    def search_similar_titles(self, title, limit=5):
        # mock fallback
        return []

@pytest.fixture
def normalizer():
    repo = MockCandidateRepo()
    
    # Pre-seed a candidate for testing matching
    cand1 = CanonicalProductCandidate(
        candidate_id="cand_1",
        canonical_title="SONY PLAYSTATION 5",
        canonical_brand="SONY",
        canonical_mpn="CFI-1000A01",
        canonical_gtins=["4948872415026"],
        source_count=1,
        matched_source_item_ids=["mock_raw_0"]
    )
    repo.candidates.append(cand1)
    
    title_norm = TitleNormalizer()
    id_norm = IdentifierNormalizer()
    conf_eng = MatchConfidenceEngine()
    matcher = EntityMatcher(repo, conf_eng)
    
    return CandidateNormalizer(title_norm, id_norm, matcher), repo

def test_gtin_strict_exact_match(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_1",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5 本体",
        raw_gtin="4948872415026"
    )
    
    # We didn't implement GTIN search in the mock, so we must rely on Brand+MPN for now, 
    # OR we can just inject Brand+MPN so the mock finds it, then GTIN gives it 1.0 score.
    raw.raw_brand = "SONY"
    raw.raw_mpn = "CFI-1000A01"
    
    result = norm.process(raw)
    
    assert result.candidate.candidate_id == "cand_1"
    assert result.evidence.identifier_hits.get("gtin") is True
    assert result.review_required is False

def test_brand_mpn_match(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_2",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5 CFI-1000A01",
        raw_brand="ソニー", # Should normalize to SONY
        raw_mpn="CFI-1000A01"
    )
    
    result = norm.process(raw)
    assert result.candidate.candidate_id == "cand_1"
    assert result.evidence.brand_match_score == 1.0
    assert result.evidence.mpn_match_score == 1.0
    assert result.review_required is False

def test_title_only_review_required(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_3",
        source_platform="mercari",
        source_url="http://test",
        raw_title="Some random unknown item",
    )
    
    result = norm.process(raw)
    # Should create a new candidate
    assert result.candidate.candidate_id != "cand_1"
    # But because it has no identifiers, it must be review_required
    assert result.review_required is True

def test_hyphen_no_hyphen_mpn_normalization(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_4",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5",
        raw_brand="SONY",
        raw_mpn="CFI1000A01" # No hyphen
    )
    
    result = norm.process(raw)
    # Should match existing candidate that has "CFI-1000A01"
    assert result.candidate.candidate_id == "cand_1"
    assert result.evidence.mpn_match_score == 1.0

def test_strict_gtin_conflict_no_merge(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_5",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5",
        raw_brand="SONY",
        raw_mpn="CFI-1000A01",
        raw_gtin="1111111111111" # Conflict with existing GTIN
    )
    
    result = norm.process(raw)
    assert result.candidate.candidate_id == "cand_1"
    # Evidence must flag the conflict
    assert "conflicting_strict_gtins" in result.evidence.ambiguity_flags
    # Conflict forces review
    assert result.review_required is True

def test_title_noise_removal():
    norm = TitleNormalizer()
    raw_title = "【新品】送料無料！激レア✨任天堂 Switch 即購入OK"
    cleaned = norm.normalize(raw_title)
    
    assert "新品" not in cleaned
    assert "送料無料" not in cleaned
    assert "激レア" not in cleaned
    assert "✨" not in cleaned
    assert "即購入" not in cleaned
    assert "任天堂 SWITCH" in cleaned

def test_idempotent_rerun(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_6",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5",
        raw_brand="SONY",
        raw_mpn="CFI-1000A01"
    )
    
    result1 = norm.process(raw)
    assert result1.candidate.source_count == 2 # 1 pre-seeded + 1 new
    
    # Run again
    result2 = norm.process(raw)
    # Source count shouldn't increase because it's already in matched_source_item_ids
    assert result2.candidate.source_count == 2

def test_dry_run_no_persistence(normalizer):
    norm, repo = normalizer
    raw = RawSourceItem(
        source_item_id="raw_7",
        source_platform="mercari",
        source_url="http://test",
        raw_title="PS5",
        raw_brand="SONY",
        raw_mpn="CFI-1000A01"
    )
    
    result = norm.process(raw, dry_run=True)
    # Source count shouldn't increase in a dry run
    assert result.candidate.source_count == 1
    assert "raw_7" not in result.candidate.matched_source_item_ids
