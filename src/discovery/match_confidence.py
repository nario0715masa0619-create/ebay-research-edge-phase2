from typing import Tuple, List, Dict, Any, Optional
from .models import NormalizedSourceItem, CanonicalProductCandidate, MatchEvidence, VariationDecision, BundleDecision, VariationDecisionClass, BundleDecisionClass

class MatchConfidenceEngine:
    """
    Evaluates how strongly a normalized source item matches a canonical candidate.
    Emphasizes "safe match" over "exact match".
    """
    
    @staticmethod
    def calculate_title_similarity(t1: str, t2: str) -> float:
        if not t1 or not t2:
            return 0.0
            
        set1 = set(t1.split())
        set2 = set(t2.split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def evaluate(self, item: NormalizedSourceItem, candidate: CanonicalProductCandidate,
                 variation_decision: Optional[VariationDecision] = None,
                 bundle_decision: Optional[BundleDecision] = None) -> Tuple[MatchEvidence, float]:
        evidence_id = f"ev_{item.normalized_item_id}_{candidate.candidate_id}"
        evidence = MatchEvidence(
            evidence_id=evidence_id,
            normalized_item_id=item.normalized_item_id,
            candidate_id=candidate.candidate_id
        )
        
        confidence = 0.0
        
        # 1. Strict GTIN check (Highest Confidence)
        item_gtins = set(item.strict_gtins)
        cand_gtins = set(candidate.canonical_gtins)
        
        if item_gtins and cand_gtins:
            if item_gtins.intersection(cand_gtins):
                confidence = 1.0
                evidence.identifier_hits["gtin"] = True
            else:
                # Conflicting strict GTINs is a major red flag
                evidence.ambiguity_flags.append("conflicting_strict_gtins")
                confidence = 0.0
                evidence.identifier_hits["gtin"] = False
        
        # 2. Brand + MPN check
        brand_match = False
        if item.normalized_brand and candidate.canonical_brand:
            if item.normalized_brand == candidate.canonical_brand:
                brand_match = True
                evidence.brand_match_score = 1.0
                
        mpn_match = False
        if item.normalized_mpn and candidate.canonical_mpn:
            # Strip hyphens for safe comparison
            item_mpn_clean = item.normalized_mpn.replace("-", "")
            cand_mpn_clean = candidate.canonical_mpn.replace("-", "")
            if item_mpn_clean == cand_mpn_clean:
                mpn_match = True
                evidence.mpn_match_score = 1.0

        if brand_match and mpn_match and confidence < 0.9:
            confidence = 0.9
            evidence.identifier_hits["brand_mpn"] = True

        # 3. Title similarity fallback
        title_sim = self.calculate_title_similarity(item.normalized_title, candidate.canonical_title)
        evidence.title_similarity_score = title_sim
        
        if confidence == 0.0 and title_sim > 0.6:
            # Soft match, requires review
            confidence = 0.6 + (title_sim * 0.3)  # Max 0.9
            evidence.ambiguity_flags.append("soft_match_title_only")
            
        # 4. Apply Variation & Bundle Penalties (Phase B)
        if variation_decision:
            evidence.variation_penalty = variation_decision.penalty_score
            confidence -= variation_decision.penalty_score
            if variation_decision.decision_class == VariationDecisionClass.CONFLICT:
                evidence.ambiguity_flags.append("variation_conflict")
            elif variation_decision.decision_class == VariationDecisionClass.AMBIGUOUS:
                evidence.ambiguity_flags.append("variation_ambiguous")
            for r in variation_decision.conflict_reasons:
                evidence.explanation_lines.append(f"Variation Issue: {r}")
                
        if bundle_decision:
            evidence.bundle_penalty = bundle_decision.penalty_score
            confidence -= bundle_decision.penalty_score
            if bundle_decision.decision_class == BundleDecisionClass.CONFLICT:
                evidence.ambiguity_flags.append("bundle_conflict")
            for r in bundle_decision.conflict_reasons:
                evidence.explanation_lines.append(f"Bundle Issue: {r}")
                
        confidence = max(0.0, confidence)
            
        # 5. Final explanation
        if confidence >= 0.95 and not evidence.ambiguity_flags:
            evidence.explanation_lines.append("Exact match via strong identifiers.")
        elif confidence >= 0.6:
            evidence.explanation_lines.append(f"Match with confidence {confidence:.2f}, possible review needed.")
        else:
            evidence.explanation_lines.append(f"Low confidence ({confidence:.2f}) or highly ambiguous match.")
            
        return evidence, confidence
