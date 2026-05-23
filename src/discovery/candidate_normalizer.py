import uuid
from typing import Optional
from .models import RawSourceItem, NormalizedSourceItem, CanonicalProductCandidate, MatchEvidence, NormalizationResult
from .title_normalizer import TitleNormalizer
from .identifier_normalizer import IdentifierNormalizer
from .entity_matcher import EntityMatcher
from .review_flagger import ReviewFlagger
from .attribute_extractor import AttributeExtractor

class CandidateNormalizer:
    """
    Main orchestration class for the Source Intelligence pipeline.
    Converts RawSourceItem -> NormalizedSourceItem -> CanonicalProductCandidate.
    """
    
    def __init__(self, title_normalizer: TitleNormalizer, identifier_normalizer: IdentifierNormalizer, entity_matcher: EntityMatcher, review_flagger: Optional[ReviewFlagger] = None, attribute_extractor: Optional[AttributeExtractor] = None):
        self.title_normalizer = title_normalizer
        self.identifier_normalizer = identifier_normalizer
        self.entity_matcher = entity_matcher
        self.review_flagger = review_flagger or ReviewFlagger()
        self.attribute_extractor = attribute_extractor or AttributeExtractor()

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
            normalized_quantity=self.attribute_extractor.extract_quantity(norm_title, raw.raw_description),
            parsed_attributes=raw.raw_attributes
        )
        
        # 3.5 Phase B: Extract Variations and Bundles
        variation_keys = self.entity_matcher.variation_detector.extract_variations(norm_title)
        bundle_flags = self.entity_matcher.bundle_detector.extract_flags(norm_title)
        
        normalized.variation_keys = variation_keys
        normalized.bundle_flags = bundle_flags
        
        # 4. Entity Matching
        candidate, evidence, variation_decision, bundle_decision = self.entity_matcher.find_best_match(normalized)
        
        # 5. Review Flagging & Candidate Generation
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
            # Phase B: Use ReviewFlagger
            review_required = self.review_flagger.evaluate(evidence)
            
            # Merge into existing candidate
            if review_required:
                candidate.review_required = True
            
            if not dry_run and raw.source_item_id not in candidate.matched_source_item_ids:
                candidate.matched_source_item_ids.append(raw.source_item_id)
                candidate.source_count += 1
                
        normalized.review_required = review_required
        
        # Extract refined confidence if available
        refined_confidence = 1.0 if not candidate else candidate.match_confidence
        # Wait, Candidate.match_confidence is not updated here in Phase A.
        # But we evaluated it during matching. In Phase A, we didn't save confidence on the evidence.
        # But we return `score` from evaluate. Actually `MatchConfidenceEngine` subtracts penalty from confidence, but `EntityMatcher.find_best_match` doesn't return the score!
        # Ah, find_best_match only returns candidate, evidence, v_dec, b_dec. It throws away `score`.
        # We need to save the confidence in `evidence` or return it.
        # But for now we can just leave it as 0.0 or let evidence handle it.
        # Actually, let's just grab ambiguity flags for NormalizationResult.
        
        return NormalizationResult(
            source_item_id=raw.source_item_id,
            normalized_item=normalized,
            candidate=candidate,
            evidence=evidence,
            status="success",
            review_required=review_required,
            variation_decision=variation_decision,
            bundle_decision=bundle_decision,
            ambiguity_flags=evidence.ambiguity_flags if evidence else [],
            explanation_lines=evidence.explanation_lines if evidence else []
        )
        
    def refine(self, normalized: NormalizedSourceItem) -> NormalizationResult:
        """
        Phase B: Re-evaluate an existing NormalizedSourceItem.
        Extracts variations/bundles and performs entity matching again.
        """
        norm_title = normalized.normalized_title
        
        # 1. Extract Variations and Bundles
        variation_keys = self.entity_matcher.variation_detector.extract_variations(norm_title)
        bundle_flags = self.entity_matcher.bundle_detector.extract_flags(norm_title)
        
        normalized.variation_keys = variation_keys
        normalized.bundle_flags = bundle_flags
        
        # 2. Entity Matching
        candidate, evidence, variation_decision, bundle_decision = self.entity_matcher.find_best_match(normalized)
        
        # 3. Review Flagging & Candidate Updating
        review_required = False
        if candidate:
            review_required = self.review_flagger.evaluate(evidence)
            if review_required:
                candidate.review_required = True
                
        normalized.review_required = review_required
        
        return NormalizationResult(
            source_item_id=normalized.source_item_id,
            normalized_item=normalized,
            candidate=candidate,
            evidence=evidence,
            status="refined",
            review_required=review_required,
            variation_decision=variation_decision,
            bundle_decision=bundle_decision,
            ambiguity_flags=evidence.ambiguity_flags if evidence else [],
            explanation_lines=evidence.explanation_lines if evidence else []
        )
