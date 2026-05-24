from typing import Tuple, List
from .models import MarketSearchSeed, MarketListingSnapshot

class AlignmentEvaluator:
    """
    Evaluates the alignment (similarity / correctness) between the original candidate seed
    and a returned MarketListingSnapshot.
    Returns scores from 0.0 to 1.0, and flags for variations/bundles.
    """
    
    def evaluate_category(self, seed: MarketSearchSeed, snapshot: MarketListingSnapshot) -> float:
        """
        Evaluate category alignment.
        If we don't have good category candidates in seed, we assume partial alignment to avoid punishing.
        """
        if not snapshot.category_path:
            return 0.5
            
        if not seed.category_candidates:
            return 1.0 # No constraint
            
        snap_cat = snapshot.category_path.lower()
        
        # Exact or partial match
        for cat in seed.category_candidates:
            c = cat.lower()
            if c in snap_cat or snap_cat in c:
                return 1.0
                
        # If words overlap
        snap_words = set(snap_cat.replace(">", " ").replace("/", " ").split())
        for cat in seed.category_candidates:
            c_words = set(cat.lower().replace(">", " ").replace("/", " ").split())
            if snap_words & c_words:
                return 0.7
                
        return 0.2 # low alignment

    def evaluate_condition(self, seed: MarketSearchSeed, snapshot: MarketListingSnapshot) -> float:
        if not snapshot.condition:
            return 0.5
            
        snap_cond = snapshot.condition.lower()
        seed_family = seed.condition_family.lower()
        
        # New
        if seed_family == "new":
            if "new" in snap_cond or "brand" in snap_cond or "unopened" in snap_cond or "sealed" in snap_cond:
                return 1.0
            if "open box" in snap_cond or "like new" in snap_cond:
                return 0.5
            return 0.1 # likely used
            
        # Used
        if seed_family == "used":
            if "new" in snap_cond and not "like new" in snap_cond:
                return 0.1 # New item in used search
            if "parts" in snap_cond or "repair" in snap_cond or "broken" in snap_cond or "junk" in snap_cond:
                return 0.2
            return 1.0
            
        return 0.5

    def evaluate_attributes(self, seed: MarketSearchSeed, snapshot: MarketListingSnapshot) -> Tuple[float, List[str], List[str]]:
        """
        Returns (score, variation_flags, bundle_flags).
        """
        score = 1.0
        v_flags = []
        b_flags = []
        title = snapshot.title.lower()
        
        # Variation mismatch check
        if seed.variation_signature:
            # If seed has a specific variation (e.g. 64GB), we want to make sure the listing doesn't contradict it
            # e.g., if seed is "64GB" and listing says "256GB", that's a conflict
            pass # A full implementation would compare extracted capacities/colors.
            
        # Common variation exclusions (capacity mismatch proxy)
        # If the seed explicitly mentions a capacity, and the listing mentions a DIFFERENT capacity
        capacities = ["64gb", "128gb", "256gb", "512gb", "1tb", "2tb"]
        seed_q = seed.keyword_query.lower()
        
        seed_caps = [c for c in capacities if c in seed_q]
        title_caps = [c for c in capacities if c in title]
        
        if seed_caps and title_caps:
            if seed_caps[0] not in title_caps:
                score *= 0.1
                v_flags.append(f"capacity_mismatch: seed={seed_caps[0]}, listing={title_caps[0]}")
                
        # Bundle / empty box check
        # Specifically look for "box only" or "empty box"
        if "only" in title and ("box only" in title or "empty box" in title):
            if not ("only" in seed_q or "box" in seed_q.split()):
                score *= 0.1
                b_flags.append("suspected_box_only_or_accessory")
                
        if "lot of" in title or "bulk" in title.split():
            if not ("lot" in seed_q or "bulk" in seed_q.split()):
                score *= 0.3
                b_flags.append("suspected_lot")

        return score, v_flags, b_flags
