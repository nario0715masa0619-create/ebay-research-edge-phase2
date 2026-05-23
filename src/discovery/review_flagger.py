from src.discovery.models import MatchEvidence

class ReviewFlagger:
    """
    Evaluates MatchEvidence and normalization penalties to determine if a candidate
    merge requires manual review, enforcing the 'Safe match over exact match' rule.
    """
    
    def evaluate(self, evidence: MatchEvidence) -> bool:
        """
        Return True if review is required.
        """
        if not evidence:
            return True
            
        # 1. Any explicit ambiguity flags trigger review
        if evidence.ambiguity_flags:
            return True
            
        # 2. Variation or Bundle penalties that are considered 'strong'
        # Variation ambiguous penalty is 0.4
        if evidence.variation_penalty >= 0.4:
            return True
            
        # Bundle penalty > 0.0 (even accessory differences) trigger review
        if evidence.bundle_penalty >= 0.5:
            return True
            
        # 3. Soft match fallback
        # If we lack strict identifiers (GTIN or Brand+MPN), we force a review
        has_strict_id = evidence.identifier_hits.get("gtin") or \
                        (evidence.brand_match_score == 1.0 and evidence.mpn_match_score == 1.0)
                        
        if not has_strict_id:
            # Relying solely on title is dangerous, flag for review
            return True
            
        return False
