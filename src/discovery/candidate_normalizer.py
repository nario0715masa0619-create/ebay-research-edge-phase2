import uuid
from typing import Optional
from .models import RawSourceItem, NormalizedSourceItem, CanonicalProductCandidate, MatchEvidence, NormalizationResult
from .title_normalizer import TitleNormalizer
from .identifier_normalizer import IdentifierNormalizer
from .entity_matcher import EntityMatcher

class CandidateNormalizer:
    """
    Main orchestration class for the Source Intelligence pipeline.
    Converts RawSourceItem -> NormalizedSourceItem -> CanonicalProductCandidate.
    """
    
    def __init__(self, title_normalizer: TitleNormalizer, identifier_normalizer: IdentifierNormalizer, entity_matcher: EntityMatcher):
        self.title_normalizer = title_normalizer
        self.identifier_normalizer = identifier_normalizer
        self.entity_matcher = entity_matcher

    def process(self, raw: RawSourceItem, dry_run: bool = False) -> NormalizationResult:
        # 1. Title Normalization
        norm_title = self.title_normalizer.normalize(raw.raw_title)
        
        # 2. Identifier Normalization
        norm_brand = self.identifier_normalizer.normalize_brand(raw.raw_brand)
        norm_mpn = self.identifier_normalizer.normalize_mpn(raw.raw_mpn)
        
        raw_gtin_list = [raw.raw_gtin] if raw.raw_gtin else []
        strict_gtins, loose_gtins = self.identifier_normalizer.normalize_gtins(raw_gtin_list)
        
        # 3. Create NormalizedSourceItem
        normalized_item_id = f"nsi_{raw.source_item_id}"
        normalized = NormalizedSourceItem(
            normalized_item_id=normalized_item_id,
            source_item_id=raw.source_item_id,
            normalized_title=norm_title,
            normalized_brand=norm_brand,
            normalized_model=self.identifier_normalizer.normalize_mpn(raw.raw_model),
            normalized_mpn=norm_mpn,
            strict_gtins=strict_gtins,
            loose_gtins=loose_gtins,
            normalized_condition=raw.raw_condition_text,
            normalized_quantity=None, # Extractor logic omitted for brevity in Phase A
            parsed_attributes=raw.raw_attributes
        )
        
        # 4. Entity Matching
        candidate, evidence = self.entity_matcher.find_best_match(normalized)
        
        # 5. Review Flagging & Candidate Generation
        review_required = False
        if not candidate:
            # Create a new canonical candidate if no match
            cand_id = f"cand_{uuid.uuid4().hex[:12]}"
            candidate = CanonicalProductCandidate(
                candidate_id=cand_id,
                canonical_title=norm_title,
                canonical_brand=norm_brand,
                canonical_model=normalized.normalized_model,
                canonical_mpn=norm_mpn,
                canonical_gtins=strict_gtins,
                canonical_condition_family="new" if "新品" in (raw.raw_condition_text or "") else "used",
                source_count=1,
                matched_source_item_ids=[raw.source_item_id],
                match_confidence=1.0,
                review_required=True if not strict_gtins and not (norm_brand and norm_mpn) else False
            )
            
            evidence = MatchEvidence(
                evidence_id=f"ev_{normalized_item_id}_new",
                normalized_item_id=normalized_item_id,
                candidate_id=cand_id,
                title_similarity_score=1.0,
                explanation_lines=["No existing candidate found. Created new candidate."]
            )
            
            review_required = candidate.review_required
        else:
            # Merge into existing candidate
            if evidence and evidence.ambiguity_flags:
                review_required = True
                candidate.review_required = True
            
            if not dry_run and raw.source_item_id not in candidate.matched_source_item_ids:
                candidate.matched_source_item_ids.append(raw.source_item_id)
                candidate.source_count += 1
                
        normalized.review_required = review_required
        
        return NormalizationResult(
            source_item_id=raw.source_item_id,
            normalized_item=normalized,
            candidate=candidate,
            evidence=evidence,
            status="success",
            review_required=review_required
        )
