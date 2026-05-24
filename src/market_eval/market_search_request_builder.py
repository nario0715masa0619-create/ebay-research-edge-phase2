from typing import Optional, Tuple, List
from .models import MarketSearchSeed, MarketSearchRequest

class MarketSearchRequestBuilder:
    """
    Builds a MarketSearchRequest from a MarketSearchSeed.
    Enforces the safe identity priority rules:
    1. strict GTIN
    2. Brand + MPN
    3. Brand + Model
    4. canonical title
    """
    
    def build(self, seed: MarketSearchSeed, limit: int = 50) -> Tuple[MarketSearchRequest, List[str]]:
        """
        Returns the built request and the evidence lines explaining the seed selection.
        """
        evidence_lines = []
        query = ""
        
        # Priority 1: GTIN
        if seed.gtins:
            # We use the first strict GTIN
            query = seed.gtins[0]
            evidence_lines.append(f"Seed strategy: GTIN ({query})")
            
        # Priority 2: Brand + MPN
        elif seed.brand and seed.mpn:
            query = f"{seed.brand} {seed.mpn}"
            evidence_lines.append(f"Seed strategy: Brand + MPN ({query})")
            
        # Priority 3: Brand + Model
        elif seed.brand and seed.model:
            query = f"{seed.brand} {seed.model}"
            evidence_lines.append(f"Seed strategy: Brand + Model ({query})")
            
        # Priority 4: Title Fallback
        else:
            query = seed.keyword_query
            evidence_lines.append(f"Seed strategy: Title Fallback ({query})")
            if "variation_conflict" in seed.risk_flags or "bundle_conflict" in seed.risk_flags:
                evidence_lines.append("Warning: Title fallback used on candidate with high ambiguity risks.")
                
        # Handle exclusions
        excluded = seed.excluded_keywords or []
        if excluded:
            # e.g., "Sony PS5 -box -only"
            exclusion_str = " ".join([f"-{kw}" for kw in excluded])
            query = f"{query} {exclusion_str}"
            evidence_lines.append(f"Applied exclusions: {excluded}")

        # Basic filters
        filters = {}
        if seed.condition_family == "new":
            # standard eBay condition IDs: 1000 for New
            filters["Condition"] = "1000"
        elif seed.condition_family == "used":
            # 3000 for Used
            filters["Condition"] = "3000"
            
        request = MarketSearchRequest(
            query=query,
            excluded_keywords=excluded,
            limit=limit,
            filters=filters,
        )
        
        return request, evidence_lines
