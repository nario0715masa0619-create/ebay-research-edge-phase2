import re
from typing import Dict, Tuple, List
from src.discovery.models import VariationDecision, VariationDecisionClass

class VariationDetector:
    """
    Extracts explicit variation attributes from strings (titles) and
    determines the severity of mismatch (exact, compatible, ambiguous, conflict).
    """
    
    CAPACITY_REGEX = re.compile(r'\b(\d{1,4}\s*(?:GB|TB|MB|G|T))\b', re.IGNORECASE)
    EDITION_REGEX = re.compile(r'\b([\w\-]+(?:Edition|Version|Ver\.?|Model))\b', re.IGNORECASE)
    REGION_REGEX = re.compile(r'\b(US|EU|JP|UK|Region\s*Free|NTSC-J|NTSC-U|PAL)\b', re.IGNORECASE)
    
    KNOWN_COLORS = {
        "black", "white", "red", "blue", "green", "yellow", "pink", "purple", "grey", "gray",
        "silver", "gold", "rose gold", "midnight", "starlight", "space gray", "coral", "cyan", "magenta"
    }

    def extract_variations(self, text: str) -> Dict[str, str]:
        """Extract recognizable variations from text."""
        if not text:
            return {}
            
        variations = {}
        text_lower = text.lower()
        
        # Extract Capacity
        cap_match = self.CAPACITY_REGEX.search(text_lower)
        if cap_match:
            # normalize spaces
            variations["capacity"] = cap_match.group(1).replace(" ", "").upper()
            
        # Extract Edition
        ed_match = self.EDITION_REGEX.search(text)
        if ed_match:
            variations["edition"] = ed_match.group(1).lower()
            
        # Extract Region
        reg_match = self.REGION_REGEX.search(text)
        if reg_match:
            variations["region"] = reg_match.group(1).upper()
            
        # Extract Color (Simple exact word matching for safety)
        tokens = re.split(r'\W+', text_lower)
        for token in tokens:
            if token in self.KNOWN_COLORS:
                variations["color"] = token
                break # Just take the first matching color for now
                
        return variations

    def compare(self, source_vars: Dict[str, str], candidate_vars: Dict[str, str]) -> VariationDecision:
        """
        Compare two sets of variations and return a decision based on Phase B specs:
        - hard blocker (capacity, size, edition, region) -> CONFLICT
        - strong penalty (color, accessories) -> AMBIGUOUS
        - soft penalty (minor string diffs) -> COMPATIBLE
        - matching -> EXACT
        """
        if not source_vars and not candidate_vars:
            return VariationDecision(decision_class=VariationDecisionClass.EXACT, penalty_score=0.0)
            
        conflict_reasons = []
        is_conflict = False
        is_ambiguous = False
        is_compatible = False
        
        all_keys = set(source_vars.keys()).union(set(candidate_vars.keys()))
        
        for key in all_keys:
            s_val = source_vars.get(key)
            c_val = candidate_vars.get(key)
            
            # If one is missing but the other has it, it's ambiguous or compatible depending on safety.
            # For Phase B, if capacity is present in one but missing in other, we flag it as ambiguous.
            # If both present and mismatch -> conflict.
            if s_val and c_val:
                if s_val != c_val:
                    if key in ["capacity", "size", "edition", "region", "bundle_count", "lot_count"]:
                        is_conflict = True
                        conflict_reasons.append(f"{key} mismatch: {s_val} vs {c_val}")
                    elif key in ["color", "included_accessories"]:
                        is_ambiguous = True
                        conflict_reasons.append(f"{key} mismatch: {s_val} vs {c_val}")
                    else:
                        is_compatible = True
            elif s_val or c_val:
                # One is missing
                if key in ["capacity", "size", "edition", "region"]:
                    # Missing capacity when the candidate has one is dangerous. Flag as ambiguous.
                    is_ambiguous = True
                    conflict_reasons.append(f"missing {key} context")
                elif key == "color":
                    is_compatible = True # Missing color is just a soft penalty
                    
        # Resolve class
        if is_conflict:
            return VariationDecision(
                decision_class=VariationDecisionClass.CONFLICT,
                penalty_score=1.0,
                conflict_reasons=conflict_reasons
            )
        elif is_ambiguous:
            return VariationDecision(
                decision_class=VariationDecisionClass.AMBIGUOUS,
                penalty_score=0.4,
                conflict_reasons=conflict_reasons
            )
        elif is_compatible or source_vars != candidate_vars:
            return VariationDecision(
                decision_class=VariationDecisionClass.COMPATIBLE,
                penalty_score=0.1,
                conflict_reasons=conflict_reasons
            )
            
        return VariationDecision(decision_class=VariationDecisionClass.EXACT, penalty_score=0.0)
