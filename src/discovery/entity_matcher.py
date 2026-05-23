from typing import Optional, Tuple
from .models import NormalizedSourceItem, CanonicalProductCandidate, MatchEvidence
from .match_confidence import MatchConfidenceEngine

class EntityMatcher:
    """
    Searches for existing canonical candidates and evaluates them using the MatchConfidenceEngine.
    """
    
    def __init__(self, candidate_repo, confidence_engine: MatchConfidenceEngine):
        self.candidate_repo = candidate_repo
        self.confidence_engine = confidence_engine

    def find_best_match(self, item: NormalizedSourceItem) -> Tuple[Optional[CanonicalProductCandidate], Optional[MatchEvidence]]:
        # 1. Search by strict GTINs
        for gtin in item.strict_gtins:
            # We assume find_by_gtin exists or we can mock it. For Phase A, we can search by Brand/MPN primarily if GTIN isn't fully indexed,
            # but let's assume we can search by GTIN eventually. For now, we will rely on brand/mpn for fast exact search in Phase A.
            pass
            
        # 2. Search by Brand + MPN
        candidate = None
        if item.normalized_brand and item.normalized_mpn:
            candidate = self.candidate_repo.find_by_brand_mpn(item.normalized_brand, item.normalized_mpn)
            
        # 3. If no Brand+MPN match, fallback to Title Search
        if not candidate and item.normalized_title:
            # Use basic prefix or ILIKE search
            candidates = self.candidate_repo.search_similar_titles(item.normalized_title, limit=5)
            best_score = 0.0
            best_cand = None
            best_ev = None
            for c in candidates:
                ev, score = self.confidence_engine.evaluate(item, c)
                if score > best_score:
                    best_score = score
                    best_cand = c
                    best_ev = ev
            if best_cand and best_score >= 0.6:
                return best_cand, best_ev
            return None, None
            
        # If Brand+MPN matched, evaluate it
        if candidate:
            evidence, score = self.confidence_engine.evaluate(item, candidate)
            if score >= 0.6:
                return candidate, evidence
                
        return None, None
