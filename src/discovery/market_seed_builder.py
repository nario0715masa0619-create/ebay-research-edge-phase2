from typing import List
from src.discovery.models import CanonicalProductCandidate
from src.discovery.scoring_contract import MarketSearchSeed
import re

class MarketSeedBuilder:
    """
    Builds safe and conservative eBay market search seeds from Canonical Candidates.
    Prioritizes strong identifiers and avoids generating unsafe wide searches for ambiguous items.
    """
    
    def build_seed(self, candidate: CanonicalProductCandidate) -> MarketSearchSeed:
        # 1. Base keyword seed
        # Fallback to canonical title if identifiers are sparse, but keep it clean
        keyword_seed = candidate.canonical_title
        
        # 2. Strong Identifiers
        brand = candidate.canonical_brand
        model = candidate.canonical_model
        mpn = candidate.canonical_mpn
        gtins = candidate.canonical_gtins
        
        # Construct safer keyword if brand + mpn/model exist
        if brand and (mpn or model):
            keyword_seed = f"{brand} {mpn or model}"
            
        excluded_keywords = []
        
        # 3. Handle Variation & Bundle Ambiguity
        # If candidate has variation conflicts flagged, we should restrict the seed
        # For Phase C, we look at ambiguity flags
        has_variation_ambiguity = any("variation" in flag for flag in candidate.ambiguity_flags)
        has_bundle_ambiguity = any("bundle" in flag for flag in candidate.ambiguity_flags)
        
        # If highly ambiguous, we don't aggressively search by raw title, 
        # we rely ONLY on MPN/GTIN if available, else we append safe keywords.
        if has_variation_ambiguity and not (mpn or gtins):
            # Extremely unsafe seed. Return minimal keyword.
            keyword_seed = keyword_seed.split()[0] if keyword_seed else ""
            
        if has_bundle_ambiguity:
            # Explicitly exclude lot/set words if we are a single item, but candidate signature might be mixed.
            # Safety-first: exclude common bundle noise unless the candidate IS explicitly a bundle.
            if "set" not in str(candidate.bundle_signature).lower() and "lot" not in str(candidate.bundle_signature).lower():
                excluded_keywords.extend(["set", "lot", "bundle", "bulk", "まとめ", "セット"])
                
        # 4. Filter Noise from Keyword Seed
        # Strip common stop words or Japanese condition noise from keyword seed to keep it canonical
        keyword_seed = re.sub(r'(?i)(新品|未使用|中古|美品|ジャンク)', '', keyword_seed).strip()
        
        # Ensure variations are appended if known and clean
        if candidate.variation_signature and not has_variation_ambiguity:
            keyword_seed = f"{keyword_seed} {candidate.variation_signature}".strip()
            
        return MarketSearchSeed(
            keyword_seed=keyword_seed,
            brand_seed=brand,
            model_seed=model,
            mpn_seed=mpn,
            gtin_seeds=gtins,
            category_candidate_seeds=candidate.category_candidates,
            item_aspects_candidate_seed=candidate.feature_payload,
            excluded_keywords=excluded_keywords
        )
