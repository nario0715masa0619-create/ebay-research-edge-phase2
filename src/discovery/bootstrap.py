from typing import Any
from .title_normalizer import TitleNormalizer
from .identifier_normalizer import IdentifierNormalizer
from .match_confidence import MatchConfidenceEngine
from .entity_matcher import EntityMatcher
from .candidate_normalizer import CandidateNormalizer

class DiscoveryContainer:
    """Dependency Injection container for the Discovery layer."""
    def __init__(self, candidate_repo: Any, normalized_item_repo: Any, match_evidence_repo: Any):
        self.candidate_repo = candidate_repo
        self.normalized_item_repo = normalized_item_repo
        self.match_evidence_repo = match_evidence_repo
        
        self.title_normalizer = TitleNormalizer()
        self.identifier_normalizer = IdentifierNormalizer()
        self.match_confidence_engine = MatchConfidenceEngine()
        
        self.entity_matcher = EntityMatcher(
            candidate_repo=self.candidate_repo,
            confidence_engine=self.match_confidence_engine
        )
        
        self.candidate_normalizer = CandidateNormalizer(
            title_normalizer=self.title_normalizer,
            identifier_normalizer=self.identifier_normalizer,
            entity_matcher=self.entity_matcher
        )

class DiscoveryBootstrap:
    _container = None
    
    @classmethod
    def get_container(cls, session_factory=None) -> DiscoveryContainer:
        if cls._container is None:
            if session_factory is None:
                raise ValueError("session_factory is required for first-time bootstrap initialization.")
                
            from src.repositories.persistent_canonical_candidate_repository import PersistentCanonicalCandidateRepository
            from src.repositories.persistent_normalized_source_item_repository import PersistentNormalizedSourceItemRepository
            from src.repositories.persistent_match_evidence_repository import PersistentMatchEvidenceRepository
            
            candidate_repo = PersistentCanonicalCandidateRepository(session_factory)
            item_repo = PersistentNormalizedSourceItemRepository(session_factory)
            ev_repo = PersistentMatchEvidenceRepository(session_factory)
            
            cls._container = DiscoveryContainer(candidate_repo, item_repo, ev_repo)
            
        return cls._container
