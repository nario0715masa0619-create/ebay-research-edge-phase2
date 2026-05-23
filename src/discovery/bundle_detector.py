import re
from typing import Dict, List
from src.discovery.models import BundleDecision, BundleDecisionClass

class BundleDetector:
    """
    Detects bundle, set, lot, and accessory flags from titles and determines
    mismatch penalties.
    """
    
    SET_REGEX = re.compile(r'セット|\bset\b|\bx\s?\d+\b|\b\d+\s?pcs\b', re.IGNORECASE)
    LOT_REGEX = re.compile(r'まとめ売り|引退品|大量|\blot\b|\bbulk\b', re.IGNORECASE)
    ACCESSORY_REGEX = re.compile(r'おまけ|付属品|ソフト付き|\bwith\s+accessories\b', re.IGNORECASE)
    SOLE_REGEX = re.compile(r'本体のみ|\bconsole\s+only\b|\bdevice\s+only\b', re.IGNORECASE)
    
    def extract_flags(self, text: str) -> List[str]:
        """Extract bundle flags from text."""
        flags = []
        if not text:
            return flags
            
        if self.SET_REGEX.search(text):
            flags.append("set")
        if self.LOT_REGEX.search(text):
            flags.append("lot")
        if self.ACCESSORY_REGEX.search(text):
            flags.append("with_accessories")
        if self.SOLE_REGEX.search(text):
            flags.append("sole_item")
            
        return flags

    def compare(self, source_flags: List[str], candidate_flags: List[str]) -> BundleDecision:
        """
        Compare bundle flags based on Phase B specs:
        - single vs set -> CONFLICT
        - lot vs single -> CONFLICT
        - accessories diff -> AMBIGUOUS
        """
        if not source_flags and not candidate_flags:
            return BundleDecision(decision_class=BundleDecisionClass.SINGLE, penalty_score=0.0)
            
        s_set = set(source_flags)
        c_set = set(candidate_flags)
        
        conflict_reasons = []
        is_conflict = False
        is_ambiguous = False
        
        # Check single vs set/lot
        s_is_single = not ("set" in s_set or "lot" in s_set)
        c_is_single = not ("set" in c_set or "lot" in c_set)
        
        if s_is_single != c_is_single:
            is_conflict = True
            conflict_reasons.append("Single vs Set/Lot mismatch")
            
        # Check explicit sole vs accessories
        if ("sole_item" in s_set and "with_accessories" in c_set) or \
           ("with_accessories" in s_set and "sole_item" in c_set):
            is_conflict = True
            conflict_reasons.append("Sole item vs Accessories included mismatch")
            
        # Check minor accessory differences
        elif ("with_accessories" in s_set) != ("with_accessories" in c_set):
            is_ambiguous = True
            conflict_reasons.append("Accessory inclusion ambiguity")
            
        if is_conflict:
            return BundleDecision(
                decision_class=BundleDecisionClass.CONFLICT,
                penalty_score=1.0,
                conflict_reasons=conflict_reasons
            )
        elif is_ambiguous:
            return BundleDecision(
                decision_class=BundleDecisionClass.CONFLICT, 
                penalty_score=0.5,
                conflict_reasons=conflict_reasons
            )
            
        # Determine actual class if they match
        base_class = BundleDecisionClass.SINGLE
        if "lot" in s_set:
            base_class = BundleDecisionClass.LOT
        elif "set" in s_set:
            base_class = BundleDecisionClass.SET
            
        return BundleDecision(decision_class=base_class, penalty_score=0.0)
