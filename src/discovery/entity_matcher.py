from typing import Optional, Tuple
from .models import NormalizedSourceItem, CanonicalProductCandidate, MatchEvidence, VariationDecision, BundleDecision
from .match_confidence import MatchConfidenceEngine
from .variation_detector import VariationDetector
from .bundle_detector import BundleDetector

class EntityMatcher:
    """
    Searches for existing canonical candidates and evaluates them using the MatchConfidenceEngine.
    """
    
    def __init__(self, candidate_repo, confidence_engine: MatchConfidenceEngine,
                 variation_detector: Optional[VariationDetector] = None,
                 bundle_detector: Optional[BundleDetector] = None):
        self.candidate_repo = candidate_repo
        self.confidence_engine = confidence_engine
        self.variation_detector = variation_detector or VariationDetector()
        self.bundle_detector = bundle_detector or BundleDetector()

    def find_best_match(self, item: NormalizedSourceItem) -> Tuple[Optional[CanonicalProductCandidate], Optional[MatchEvidence], Optional[VariationDecision], Optional[BundleDecision]]:
        # 1. Search by strict GTINs
        for gtin in item.strict_gtins:
            # We assume find_by_gtin exists or we can mock it. For Phase A, we can search by Brand/MPN primarily if GTIN isn't fully indexed,
            # but let's assume we can search by GTIN eventually. For now, we will rely on brand/mpn for fast exact search in Phase A.
            pass
            
        # 2. Search by Brand + MPN
        candidate = None
        if item.normalized_brand and item.normalized_mpn:
            candidate = self.candidate_repo.find_by_brand_mpn(item.normalized_brand, item.normalized_mpn)
            
        # Helper to evaluate candidate with Phase B detectors
        def _eval_with_phase_b(cand: CanonicalProductCandidate) -> Tuple[MatchEvidence, float, VariationDecision, BundleDecision]:
            cand_vars = self.variation_detector.extract_variations(cand.canonical_title)
            cand_bundles = self.bundle_detector.extract_flags(cand.canonical_title)
            v_dec = self.variation_detector.compare(item.variation_keys, cand_vars)
            b_dec = self.bundle_detector.compare(item.bundle_flags, cand_bundles)
            ev, score = self.confidence_engine.evaluate(item, cand, v_dec, b_dec)
            return ev, score, v_dec, b_dec
            
        # 3. If no Brand+MPN match, fallback to Title Search
        if not candidate and item.normalized_title:
            candidates = self.candidate_repo.search_similar_titles(item.normalized_title, limit=5)
            best_score = 0.0
            best_cand, best_ev, best_v_dec, best_b_dec = None, None, None, None
            for c in candidates:
                ev, score, v_dec, b_dec = _eval_with_phase_b(c)
                if score > best_score:
                    best_score = score
                    best_cand = c
                    best_ev = ev
                    best_v_dec = v_dec
                    best_b_dec = b_dec
            if best_cand and best_score >= 0.6:
                return best_cand, best_ev, best_v_dec, best_b_dec
            return None, None, None, None
            
        # If Brand+MPN matched, evaluate it
        if candidate:
            evidence, score, v_dec, b_dec = _eval_with_phase_b(candidate)
            if score >= 0.6:
                return candidate, evidence, v_dec, b_dec
                
        return None, None, None, None
