import re
from typing import Tuple, List, Optional

class IdentifierNormalizer:
    """
    Cleans and standardizes GTINs, MPNs, and Brands.
    Separates strict identifiers (safe for auto-merge) from loose ones (auxiliary signals).
    """
    
    # Common brand aliases for Phase A
    BRAND_ALIASES = {
        "NINTENDO": "NINTENDO",
        "任天堂": "NINTENDO",
        "SONY": "SONY",
        "ソニー": "SONY",
        "BANDAI": "BANDAI",
        "バンダイ": "BANDAI",
    }
    
    @classmethod
    def normalize_brand(cls, raw_brand: Optional[str]) -> Optional[str]:
        if not raw_brand:
            return None
            
        brand = raw_brand.strip().upper()
        return cls.BRAND_ALIASES.get(brand, brand)

    @classmethod
    def normalize_mpn(cls, raw_mpn: Optional[str]) -> Optional[str]:
        if not raw_mpn:
            return None
            
        # Upper case, remove spaces
        mpn = raw_mpn.strip().upper()
        mpn = re.sub(r'\s+', '', mpn)
        
        # We preserve hyphens because they often matter in MPNs (e.g. CUH-2000A vs CUH2000A), 
        # but for matching we might need a hyphen-insensitive comparison later.
        # For canonicalization, we keep the hyphen if the source provided it.
        return mpn if mpn else None

    @classmethod
    def normalize_gtins(cls, raw_gtins: List[str]) -> Tuple[List[str], List[str]]:
        """
        Parses a list of raw GTIN candidates.
        Returns: (strict_gtins, loose_gtins)
        """
        strict = []
        loose = []
        
        for gtin in raw_gtins:
            if not gtin:
                continue
                
            # Strip non-digits
            cleaned = re.sub(r'\D', '', str(gtin))
            if not cleaned:
                continue
                
            length = len(cleaned)
            # Standard GTIN lengths are 8 (EAN-8), 12 (UPC), 13 (EAN-13), 14 (GTIN-14)
            if length in [8, 12, 13, 14]:
                if cleaned not in strict:
                    strict.append(cleaned)
            else:
                # E.g., someone put a short model number as GTIN
                if cleaned not in loose:
                    loose.append(cleaned)
                    
        return strict, loose
