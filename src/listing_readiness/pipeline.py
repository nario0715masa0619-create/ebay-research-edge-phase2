import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.ebay.models import ProductCandidate, CandidateEvidence, JobRun
from .models import ListingReadinessRequest, ListingReadinessResult, ListingReadinessBatchResult

# Resolvers & Evaluators
from .category_resolver import CategoryResolver
from .aspects_resolver import AspectsResolver
from .condition_resolver import ConditionResolver
from .content_evaluator import ContentReadinessEvaluator
from .policy_evaluator import PolicyReadinessEvaluator
from .blocker_engine import BlockerEngine
from .draft_builder import ListingPayloadDraftBuilder

class ListingReadinessPipeline:
    def __init__(
        self,
        candidate_repo,
        evidence_repo,
        job_repo
    ):
        self.candidate_repo = candidate_repo
        self.evidence_repo = evidence_repo
        self.job_repo = job_repo
        
        self.category_resolver = CategoryResolver()
        self.aspects_resolver = AspectsResolver()
        self.condition_resolver = ConditionResolver()
        self.content_evaluator = ContentReadinessEvaluator()
        self.policy_evaluator = PolicyReadinessEvaluator()
        self.blocker_engine = BlockerEngine()
        self.draft_builder = ListingPayloadDraftBuilder()

    def build_listing_readiness(self, request: ListingReadinessRequest) -> ListingReadinessResult:
        candidate = self.candidate_repo.get_by_candidate_id(request.candidate_id)
        if not candidate:
            return ListingReadinessResult(
                candidate_id=request.candidate_id,
                sku="unknown",
                listing_readiness_status="error",
                publish_readiness=False,
                success_flag=False
            )

        # 0. Check manual_preban (Section 7/12)
        if candidate.pipeline_type == "manual_preban":
            status = "blocked"
            publish_ready = False
            blockers = ["manual_preban_not_supported"]
            codes = ["preban_blocked"]
            
            # Create dummy results for draft building
            from .category_resolver import CategoryResolutionResult
            from .aspects_resolver import AspectsResolutionResult
            from .condition_resolver import ConditionResolutionResult
            from .content_evaluator import ContentReadinessResult
            from .policy_evaluator import PolicyReadinessResult
            cat_res = CategoryResolutionResult()
            asp_res = AspectsResolutionResult()
            cond_res = ConditionResolutionResult()
            cont_res = ContentReadinessResult()
            pol_res = PolicyReadinessResult()
        else:
            # 13. Idempotency / 再評価制御 (Skipping if already ready)
            if candidate.listing_readiness_status == "ready" and not request.force_recheck:
                 return ListingReadinessResult(
                    candidate_id=candidate.candidate_id,
                    sku=candidate.sku,
                    listing_readiness_status=candidate.listing_readiness_status,
                    publish_readiness=candidate.publish_readiness,
                    success_flag=True
                )
            # 12. 対象 candidate 制約を守ること
            # pipeline_type == auto, decision_type in candidate, review_required, status in candidate, approved, researched
            allowed_decisions = ["candidate", "review_required"]
            allowed_statuses = ["candidate", "approved", "researched"]
            
            is_target = (
                candidate.pipeline_type == "auto" and 
                candidate.decision_type in allowed_decisions and 
                candidate.status in allowed_statuses
            )
            
            if not is_target and not request.force_recheck:
                # Skip non-target candidates unless forced
                return ListingReadinessResult(
                    candidate_id=candidate.candidate_id,
                    sku=candidate.sku,
                    listing_readiness_status=candidate.listing_readiness_status,
                    publish_readiness=candidate.publish_readiness,
                    readiness_reason_codes=["not_a_processing_target"],
                    success_flag=True
                )
            # 1. Category Resolution
            cat_res = self.category_resolver.resolve(candidate, request.marketplace_id)
            
            # 2. Condition Resolution
            cond_res = self.condition_resolver.resolve(candidate, cat_res.ebay_category_id)
            
            # 3. Aspects Resolution
            asp_res = self.aspects_resolver.resolve(candidate, cat_res.ebay_category_id or "unknown")
            
            # 4. Content Evaluation
            cont_res = self.content_evaluator.evaluate(candidate, request.title_max_length)
            
            # 5. Policy Evaluation
            pol_res = self.policy_evaluator.evaluate(candidate, request.allow_default_policy_reference)
            
            # 6. Blocker Evaluation
            status, publish_ready, blockers, codes = self.blocker_engine.evaluate(
                cat_res, asp_res, cond_res, cont_res, pol_res, request.strictness
            )
        
        # 7. Draft Building
        inv_draft = self.draft_builder.build_inventory_item_draft(candidate, asp_res, cond_res)
        off_draft = self.draft_builder.build_offer_draft(candidate, cat_res, pol_res, request.marketplace_id)
        
        # 8. Update Candidate
        candidate.ebay_category_id = cat_res.ebay_category_id
        candidate.category_tree_id = cat_res.category_tree_id
        candidate.category_tree_version = cat_res.category_tree_version
        candidate.category_confidence = cat_res.confidence
        
        candidate.ebay_condition = cond_res.ebay_condition
        candidate.condition_descriptor_json = cond_res.condition_descriptor_json
        candidate.condition_confidence = cond_res.confidence
        
        candidate.ebay_aspects_json = asp_res.ebay_aspects_json
        candidate.missing_required_aspects = asp_res.missing_required_aspects
        candidate.missing_recommended_aspects = asp_res.missing_recommended_aspects
        
        candidate.listing_readiness_status = status
        candidate.listing_blockers = blockers
        candidate.publish_readiness = publish_ready
        
        candidate.inventory_item_draft_json = inv_draft
        candidate.offer_draft_json = off_draft
        
        candidate.last_checked_at = datetime.now()
        candidate.updated_at = datetime.now()
        
        # 9. Evidence Persistence
        evidences = [
            self._make_evidence(candidate.candidate_id, "category_resolution", cat_res),
            self._make_evidence(candidate.candidate_id, "aspects_resolution", asp_res),
            self._make_evidence(candidate.candidate_id, "condition_resolution", cond_res),
            self._make_evidence(candidate.candidate_id, "content_readiness", cont_res),
            self._make_evidence(candidate.candidate_id, "policy_readiness", pol_res),
            self._make_evidence(candidate.candidate_id, "blocker_evaluation", {
                "status": status, "publish_ready": publish_ready, "blockers": blockers, "codes": codes
            }),
            self._make_evidence(candidate.candidate_id, "listing_payload_draft", {
                "inventory": inv_draft, "offer": off_draft
            })
        ]
        
        self.candidate_repo.upsert(candidate)
        self.evidence_repo.save_many(evidences)
        
        return ListingReadinessResult(
            candidate_id=candidate.candidate_id,
            sku=candidate.sku,
            listing_readiness_status=status,
            publish_readiness=publish_ready,
            ebay_category_id=cat_res.ebay_category_id,
            ebay_condition=cond_res.ebay_condition,
            ebay_aspects_json=asp_res.ebay_aspects_json,
            missing_required_aspects=asp_res.missing_required_aspects,
            missing_recommended_aspects=asp_res.missing_recommended_aspects,
            listing_blockers=blockers,
            readiness_reason_codes=codes,
            evidence_ids=[e.evidence_id for e in evidences],
            inventory_item_draft=inv_draft,
            offer_draft=off_draft,
            success_flag=True
        )

    def run_listing_readiness_pipeline(
        self,
        candidate_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        force_recheck: bool = False,
        marketplace_id: str = "EBAY_US",
        strictness: str = "balanced"
    ) -> ListingReadinessBatchResult:
        job = self.job_repo.start_run("listing_readiness_pipeline")
        
        if candidate_ids:
            candidates = [self.candidate_repo.get_by_candidate_id(cid) for cid in candidate_ids]
            candidates = [c for c in candidates if c]
        else:
            # Only process candidates that are likely to be ready
            candidates = self.candidate_repo.list_by_status("candidate", limit=limit)

        for cand in candidates:
            req = ListingReadinessRequest(
                candidate_id=cand.candidate_id,
                run_id=job.run_id,
                force_recheck=force_recheck,
                marketplace_id=marketplace_id,
                strictness=strictness
            )
            try:
                res = self.build_listing_readiness(req)
                metrics = {
                    "processed_count": 1,
                    "ready_count": 1 if res.listing_readiness_status == "ready" else 0,
                    "blocked_count": 1 if res.listing_readiness_status == "blocked" else 0,
                    "review_count": 1 if res.listing_readiness_status == "review_required" else 0,
                    "error_count": 0 if res.success_flag else 1
                }
                self.job_repo.append_progress(job.run_id, metrics)
            except Exception as e:
                self.job_repo.append_progress(job.run_id, {"processed_count": 1, "error_count": 1})
                if job.error_summary is None: job.error_summary = ""
                job.error_summary += f"{cand.candidate_id}: {str(e)}\n"

        self.job_repo.finish_run(job.run_id, "completed", {
            "processed_count": job.processed_count,
            "ready_count": job.ready_count,
            "blocked_count": job.blocked_count,
            "review_count": job.review_count,
            "error_count": job.error_count
        }, job.error_summary)

        return ListingReadinessBatchResult(
            run_id=job.run_id,
            processed_count=job.processed_count,
            ready_count=job.ready_count,
            blocked_count=job.blocked_count,
            review_count=job.review_count,
            error_count=job.error_count,
            error_summary=[job.error_summary] if job.error_summary else []
        )

    def _make_evidence(self, candidate_id: str, e_type: str, result: Any) -> CandidateEvidence:
        import dataclasses
        if dataclasses.is_dataclass(result):
            payload = dataclasses.asdict(result)
        elif isinstance(result, dict):
            payload = result
        else:
            payload = {"data": str(result)}
            
        return CandidateEvidence(
            evidence_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            evidence_type=e_type,
            evidence_payload=payload
        )
