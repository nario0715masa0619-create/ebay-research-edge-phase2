import pytest
from src.discovery.review_models import ReviewStatus
from src.discovery.alias_dictionary import AliasDictionary
from src.repositories.persistent_alias_dictionary_repository import AliasRecord
from src.discovery.market_seed_builder import MarketSeedBuilder
from src.discovery.models import CanonicalProductCandidate
from src.discovery.scoring_contract import ProfitabilityScoringInputPayload

class MockAliasRepo:
    def __init__(self, records):
        self.records = records
    def get_all_enabled_aliases(self):
        return self.records

def test_alias_dictionary_resolution():
    repo = MockAliasRepo([
        AliasRecord("1", "brand", "nintnedo", "Nintendo", None, True),
        AliasRecord("2", "model", "ps5", "PlayStation 5", None, True),
        AliasRecord("3", "noise", "美品", "", None, True),
        AliasRecord("4", "mpn_rule", r"^xyz-(.*)$", r"ABC-\1", None, True),
    ])
    alias_dict = AliasDictionary(repo)
    
    assert alias_dict.resolve_brand("Nintnedo") == "Nintendo"
    assert alias_dict.resolve_model("ps5") == "PlayStation 5"
    assert alias_dict.resolve_mpn("xyz-1234") == "ABC-1234"
    
    clean_title = alias_dict.strip_source_noise("美品 Sony Camera", "global")
    assert clean_title == "Sony Camera"

def test_market_seed_builder_safety():
    builder = MarketSeedBuilder()
    
    # 1. Normal Candidate
    cand_normal = CanonicalProductCandidate(
        candidate_id="c1",
        canonical_title="Sony PS5 Console",
        canonical_brand="Sony",
        canonical_model="PS5",
        ambiguity_flags=[]
    )
    seed1 = builder.build_seed(cand_normal)
    assert seed1.keyword_seed == "Sony PS5"
    assert "set" not in seed1.excluded_keywords
    
    # 2. Bundle Ambiguity
    cand_bundle = CanonicalProductCandidate(
        candidate_id="c2",
        canonical_title="Game Console",
        bundle_signature="single",
        ambiguity_flags=["bundle_conflict"]
    )
    seed2 = builder.build_seed(cand_bundle)
    assert "set" in seed2.excluded_keywords
    assert "lot" in seed2.excluded_keywords
    
    # 3. Variation Ambiguity (No identifiers -> severe fallback)
    cand_var = CanonicalProductCandidate(
        candidate_id="c3",
        canonical_title="Nintendo Switch Red",
        ambiguity_flags=["variation_conflict"]
    )
    seed3 = builder.build_seed(cand_var)
    # With variation conflict and no strong MPN, it truncates safely
    assert seed3.keyword_seed == "Nintendo"

def test_scoring_contract_schema():
    payload = ProfitabilityScoringInputPayload(
        candidate_id="cand_123",
        source_cost_total_jpy=15000,
        source_shipping_cost_jpy=500,
        condition_family="used",
        review_required=True,
        ambiguity_flags=["color_mismatch"]
    )
    
    assert payload.candidate_id == "cand_123"
    assert payload.source_cost_total_jpy == 15000
    assert payload.review_required is True
    assert "color_mismatch" in payload.ambiguity_flags
