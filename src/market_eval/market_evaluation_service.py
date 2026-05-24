import uuid
import logging
from typing import Tuple
from datetime import datetime, timezone

from .models import (
    MarketSearchSeed, 
    MarketSearchRequest, 
    MarketEvaluationResult, 
    MarketEvaluationEvidence
)
from .config import MarketEvalSettings
from .market_search_gateway import MarketSearchGateway
from .market_search_request_builder import MarketSearchRequestBuilder
from .search_result_normalizer import SearchResultNormalizer
from .comparable_filter import ComparableFilter
from .price_band_estimator import PriceBandEstimator
from .market_confidence import MarketConfidenceCalculator

# Assuming CanonicalProductCandidate structure from discovery layer
class MarketEvaluationService:
    """
    Main service orchestrator for the Market Evaluation Layer.
    Coordinates query building, provider search, normalization, filtering, estimation, and confidence scoring.
    """
    def __init__(
        self,
        settings: MarketEvalSettings,
        gateway: MarketSearchGateway,
        request_builder: MarketSearchRequestBuilder = None,
        normalizer: SearchResultNormalizer = None,
        comparable_filter: ComparableFilter = None,
        price_estimator: PriceBandEstimator = None,
        confidence_calc: MarketConfidenceCalculator = None,
        logger: logging.Logger = None
    ):
        self.settings = settings
        self.gateway = gateway
        self.request_builder = request_builder or MarketSearchRequestBuilder()
        self.normalizer = normalizer or SearchResultNormalizer()
        self.comparable_filter = comparable_filter or ComparableFilter()
        self.price_estimator = price_estimator or PriceBandEstimator(trim_enabled=settings.outlier_trim_enabled)
        self.confidence_calc = confidence_calc or MarketConfidenceCalculator()
        self.logger = logger or logging.getLogger(__name__)

    def _build_seed_from_candidate(self, candidate) -> MarketSearchSeed:
        # Assumes candidate is a CanonicalProductCandidateModel or dict-like
        c_id = getattr(candidate, "candidate_id", None) or candidate.get("candidate_id", "")
        q = getattr(candidate, "canonical_title", None) or candidate.get("canonical_title", "")
        brand = getattr(candidate, "canonical_brand", None) or candidate.get("canonical_brand")
        model = getattr(candidate, "canonical_model", None) or candidate.get("canonical_model")
        mpn = getattr(candidate, "canonical_mpn", None) or candidate.get("canonical_mpn")
        
        gtins = getattr(candidate, "canonical_gtins_json", []) or candidate.get("canonical_gtins_json", [])
        categories = getattr(candidate, "category_candidates_json", []) or candidate.get("category_candidates_json", [])
        cond_family = getattr(candidate, "canonical_condition_family", "used") or candidate.get("canonical_condition_family", "used")
        var_sig = getattr(candidate, "variation_signature", None) or candidate.get("variation_signature")
        bun_sig = getattr(candidate, "bundle_signature", None) or candidate.get("bundle_signature")
        ambiguity = getattr(candidate, "ambiguity_flags_json", []) or candidate.get("ambiguity_flags_json", [])
        
        # Handle dict-like fallback
        if isinstance(gtins, str):
            gtins = []

        return MarketSearchSeed(
            candidate_id=str(c_id),
            keyword_query=str(q),
            brand=str(brand) if brand else None,
            model=str(model) if model else None,
            mpn=str(mpn) if mpn else None,
            gtins=gtins,
            category_candidates=categories,
            variation_signature=str(var_sig) if var_sig else None,
            bundle_signature=str(bun_sig) if bun_sig else None,
            condition_family=str(cond_family),
            risk_flags=ambiguity
        )

    def evaluate_candidate(self, candidate) -> Tuple[MarketEvaluationResult, MarketEvaluationEvidence]:
        seed = self._build_seed_from_candidate(candidate)
        
        # 1. Build Request
        request, seed_evidence_lines = self.request_builder.build(seed, limit=self.settings.max_results)
        
        # 2. Call Provider
        gateway_response = self.gateway.search_completed_items(request)
        unsafe_reasons = list(gateway_response.unsafe_reasons)
        raw_items = gateway_response.raw_items
        raw_count = len(raw_items)
        
        # 3. Normalize
        snapshots = self.normalizer.normalize_items(raw_items)
        
        # 4. Filter
        evaluations = self.comparable_filter.filter_comparables(seed, snapshots)
        included_evals = [e for e in evaluations if e.included]
        comparables = [s for s in snapshots if any(e.listing_id == s.listing_id and e.included for e in evaluations)]
        filtered_count = len(comparables)
        
        # Collect exclusion reasons
        for e in evaluations:
            if not e.included and e.exclusion_reason:
                seed_evidence_lines.append(f"Excluded {e.listing_id}: {e.exclusion_reason}")

        # 5. Estimate Price Band
        p_low, p_med, p_high = self.price_estimator.estimate(comparables)
        
        # 6. Confidence & Proxies
        confidence, comp_proxy, dem_proxy, final_unsafe = self.confidence_calc.calculate(
            evaluations=evaluations,
            unsafe_reasons=unsafe_reasons,
            raw_count=raw_count,
            min_comparable_count=self.settings.min_comparable_count
        )
        
        # Evaluation Status
        eval_status = "success"
        review_required = False
        if confidence < 0.5 or final_unsafe:
            eval_status = "unsafe"
            review_required = True
        
        if any("provider_error" in u or "parse_failure" in u for u in final_unsafe):
            eval_status = "error"
            review_required = True

        evidence_summary = f"Evaluated {filtered_count}/{raw_count} items. Status: {eval_status}. Confidence: {confidence:.2f}"
        if final_unsafe:
            evidence_summary += f". Flags: {', '.join(final_unsafe)}"
            
        # Quality score proxy
        avg_quality = 0.0
        if included_evals:
            avg_quality = sum(e.comparable_score for e in included_evals) / len(included_evals)

        evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
        evidence_id = f"evd_me_{uuid.uuid4().hex[:12]}"
        
        result = MarketEvaluationResult(
            market_evaluation_id=evaluation_id,
            candidate_id=seed.candidate_id,
            evaluation_status=eval_status,
            comparable_count=filtered_count,
            comparable_quality_score=avg_quality,
            price_low=p_low,
            price_median=p_med,
            price_high=p_high,
            category_alignment_score=sum(e.category_alignment_score for e in included_evals) / max(1, filtered_count),
            condition_alignment_score=sum(e.condition_alignment_score for e in included_evals) / max(1, filtered_count),
            attribute_alignment_score=sum(e.attribute_alignment_score for e in included_evals) / max(1, filtered_count),
            competition_proxy=comp_proxy,
            demand_proxy=dem_proxy,
            market_confidence=confidence,
            unsafe_reasons=final_unsafe,
            review_required=review_required,
            evidence_summary=evidence_summary,
            search_queries_used=[request.query],
            raw_result_count=raw_count,
            filtered_result_count=filtered_count
        )
        
        evidence = MarketEvaluationEvidence(
            evidence_id=evidence_id,
            candidate_id=seed.candidate_id,
            search_request_payload={"query": request.query, "limit": request.limit, "filters": request.filters},
            provider_name=gateway_response.provider_name,
            comparable_listing_ids=[c.listing_id for c in comparables],
            excluded_listing_ids=[e.listing_id for e in evaluations if not e.included],
            unsafe_reasons=final_unsafe,
            evidence_lines=seed_evidence_lines,
            raw_response_reference=None # Save object storage reference if needed
        )
        
        return result, evidence
