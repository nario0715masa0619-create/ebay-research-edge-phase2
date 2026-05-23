import re
from typing import Optional, Dict, Any

class AttributeExtractor:
    """
    Extracts general attributes like quantity and condition from raw item text.
    Variation and Bundle specifics are handled by their respective detectors.
    """
    
    QTY_REGEX = re.compile(r'(\d+)\s*(?:個|点|pcs|pieces)', re.IGNORECASE)
    
    def extract_quantity(self, title: str, description: Optional[str] = None) -> Optional[int]:
        if not title:
            return None
            
        match = self.QTY_REGEX.search(title)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
                
        if description:
            match = self.QTY_REGEX.search(description)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
                    
        return None
        
    def extract_condition_family(self, condition_text: Optional[str]) -> str:
        if not condition_text:
            return "used" # Safe default
            
        text = condition_text.lower()
        if "新品" in text or "new" in text or "未開封" in text:
            return "new"
        return "used"
