from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from src.ebay.models import ProductCandidate

@dataclass
class AspectsResolutionResult:
    ebay_aspects_json: Dict[str, Any] = field(default_factory=dict)
    missing_required_aspects: List[str] = field(default_factory=list)
    missing_recommended_aspects: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reason_codes: List[str] = field(default_factory=list)

class AspectsResolver:
    def resolve(self, candidate: ProductCandidate, category_id: str) -> AspectsResolutionResult:
        # In real implementation, this would fetch metadata for category_id
        # and match candidate attributes (brand, character, etc.)
        
        aspects = {}
        missing_req = []
        missing_rec = []
        
        # Mock Logic
        if category_id == "183454": # Pokemon Cards
            aspects["Game"] = ["Pokémon TCG"]
            aspects["Language"] = ["Japanese"]
            
            if candidate.brand:
                aspects["Brand"] = [candidate.brand]
            else:
                missing_req.append("Brand")
                
            if candidate.character:
                aspects["Character"] = [candidate.character]
            else:
                missing_rec.append("Character")
        else:
            missing_req.append("Brand") # Default requirement for mock
            
        return AspectsResolutionResult(
            ebay_aspects_json=aspects,
            missing_required_aspects=missing_req,
            missing_recommended_aspects=missing_rec,
            confidence=0.8 if not missing_req else 0.3,
            reason_codes=["mock_pokemon_logic" if category_id == "183454" else "default_logic"]
        )
