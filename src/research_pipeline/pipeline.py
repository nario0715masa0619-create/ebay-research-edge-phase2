import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.ebay.models import SourceItem, ProductCandidate, CandidateEvidence, JobRun
from .models import CandidateBuildRequest, CandidateBuildResult, ResearchPipelineResult
from .builder import CandidateBuilder
from .decision_engine import CandidateDecisionEngine

# Resolvers
from src.shipping.resolver import resolve_shipping_cost
from src.import_cost.resolver import resolve_import_charges
from src.selling_fee.resolver import resolve_selling_fee
from src.payout_cost.resolver import resolve_payout_fee
from src.total_cost.resolver import resolve_total_cost
from src.score.calculator import calculate_standard_score

class CandidatePipeline:
    def __init__(
        self,
        source_repo,
        candidate_repo,
        evidence_repo,
        job_repo
    ):
        self.source_repo = source_repo
        self.candidate_repo = candidate_repo
        self.evidence_repo = evidence_repo
        self.job_repo = job_repo
        self.builder = CandidateBuilder()
        self.decision_engine = CandidateDecisionEngine()

    def build_research_candidate(self, request: CandidateBuildRequest) -> CandidateBuildResult:
        source_item = self.source_repo.get_by_id(request.source_item_id)
        if not source_item:
            return CandidateBuildResult(source_item_id=request.source_item_id, notes=["Source item not found"])

        # 1. Check for existing candidate
        existing = self.candidate_repo.get_by_source_key(source_item.source_platform, source_item.source_item_id)
        if existing and not request.force_rebuild:
            return CandidateBuildResult(
                source_item_id=request.source_item_id,
                candidate_id=existing.candidate_id,
                sku=existing.sku,
                status=existing.status,
                success_flag=True,
                notes=["Existing candidate found, skipped rebuild"]
            )

        # 2. Build Initial Candidate
        candidate = self.builder.build_initial_candidate(source_item)
        
        # 3. Apply Resolvers (Orchestration)
        evidences = []
        
        # Placeholder for Sale Price Estimation (In real tool, this calls Browse API / Search API)
        expected_sale_price_jpy = source_item.source_price_jpy * 2.0
        expected_sale_price_usd = expected_sale_price_jpy / 150.0 # Placeholder FX
        candidate.expected_sale_price_usd = expected_sale_price_usd
        candidate.expected_sale_price_jpy = expected_sale_price_jpy

        # Shipping
        ship_res = resolve_shipping_cost(
            item_id=source_item.source_item_id,
            marketplace_id=request.marketplace_id,
            delivery_country=request.delivery_country,
            quantity=request.quantity,
            fallback_shipping_value=20.0 # Default fallback
        )
        evidences.append(self._make_evidence(candidate.candidate_id, "shipping", ship_res))

        # Import
        import_res = resolve_import_charges(
            item_id=source_item.source_item_id,
            marketplace_id=request.marketplace_id,
            delivery_country=request.delivery_country,
            item_price=candidate.expected_sale_price_usd,
            shipping_estimate=getattr(ship_res, "shipping_estimated_total", 0.0),
            quantity=request.quantity,
            fallback_import_rule={"rate": 0.1, "rule_id": "default_vat"} # Default fallback
        )
        evidences.append(self._make_evidence(candidate.candidate_id, "import", import_res))

        # Selling Fee
        sell_res = resolve_selling_fee(
            marketplace_id=request.marketplace_id,
            category_id="unknown", # TODO: resolver integration
            item_price=candidate.expected_sale_price_usd,
            charged_shipping=0.0,
            collected_tax=0.0,
            quantity=request.quantity
        )
        evidences.append(self._make_evidence(candidate.candidate_id, "selling_fee", sell_res))

        # Payout Fee
        payout_res = resolve_payout_fee(
            gross_payout_amount=candidate.expected_sale_price_usd - getattr(sell_res, "selling_fee_estimated_total", 0.0),
            payout_currency="USD",
            target_bank_currency="JPY"
        )
        evidences.append(self._make_evidence(candidate.candidate_id, "payout_fee", payout_res))

        # Total Cost
        total_res = resolve_total_cost(
            procurement_item_cost=source_item.source_price_jpy / 150.0, # Placeholder FX
            sale_item_price=candidate.expected_sale_price_usd,
            shipping_result=ship_res,
            import_result=import_res,
            selling_fee_result=sell_res,
            payout_fee_result=payout_res,
            strictness=request.strictness
        )
        candidate.expected_profit_jpy = total_res.final_profit_after_all_costs * 150.0
        candidate.expected_profit_rate = total_res.estimated_margin_rate or 0.0
        evidences.append(self._make_evidence(candidate.candidate_id, "total_cost", total_res))

        # Score
        score_res = calculate_standard_score(
            total_cost_result=total_res,
            scoring_profile=request.scoring_profile,
            strictness=request.strictness
        )
        candidate.standard_score = score_res.standard_score
        candidate.score_grade = score_res.score_grade
        evidences.append(self._make_evidence(candidate.candidate_id, "score", score_res))

        # 4. Decision Engine
        pipeline_type, decision_type, exclude_reason, reason_codes = self.decision_engine.decide(candidate, request.strictness)
        candidate.pipeline_type = pipeline_type
        candidate.decision_type = decision_type
        candidate.exclude_reason = exclude_reason
        candidate.decision_reason_codes = reason_codes
        candidate.auto_listable = (decision_type == "candidate")

        # 5. Persist
        self.candidate_repo.upsert(candidate)
        self.evidence_repo.save_many(evidences)
        self.source_repo.mark_processed(source_item.source_item_id)

        return CandidateBuildResult(
            source_item_id=source_item.source_item_id,
            candidate_id=candidate.candidate_id,
            sku=candidate.sku,
            pipeline_type=pipeline_type,
            decision_type=decision_type,
            status=candidate.status,
            auto_listable=candidate.auto_listable,
            exclude_reason=exclude_reason,
            evidence_ids=[e.evidence_id for e in evidences],
            success_flag=True
        )

    def run_research_candidate_pipeline(
        self,
        source_item_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        force_rebuild: bool = False,
        strictness: str = "balanced",
        scoring_profile: str = "balanced"
    ) -> ResearchPipelineResult:
        job = self.job_repo.start_run("research_candidate_pipeline")
        
        if source_item_ids:
            items_to_process = [self.source_repo.get_by_id(sid) for sid in source_item_ids]
            items_to_process = [i for i in items_to_process if i]
        else:
            items_to_process = self.source_repo.list_unprocessed(limit=limit)

        for item in items_to_process:
            req = CandidateBuildRequest(
                source_item_id=item.source_item_id,
                run_id=job.run_id,
                force_rebuild=force_rebuild,
                strictness=strictness,
                scoring_profile=scoring_profile
            )
            try:
                res = self.build_research_candidate(req)
                metrics = {
                    "processed_count": 1,
                    "success_count": 1 if res.success_flag else 0,
                    "excluded_count": 1 if res.decision_type == "excluded" else 0,
                    "review_count": 1 if res.decision_type == "review_required" else 0,
                    "candidate_count": 1 if res.decision_type == "candidate" else 0,
                    "error_count": 0 if res.success_flag else 1
                }
                self.job_repo.append_progress(job.run_id, metrics)
            except Exception as e:
                self.job_repo.append_progress(job.run_id, {"processed_count": 1, "error_count": 1})
                if job.error_summary is None: job.error_summary = ""
                job.error_summary += f"{item.source_item_id}: {str(e)}\n"

        self.job_repo.finish_run(job.run_id, "completed", {
            "processed_count": job.processed_count,
            "success_count": job.success_count,
            "excluded_count": job.excluded_count,
            "review_count": job.review_count,
            "candidate_count": job.candidate_count,
            "error_count": job.error_count
        }, job.error_summary)

        return ResearchPipelineResult(
            run_id=job.run_id,
            processed_count=job.processed_count,
            success_count=job.success_count,
            excluded_count=job.excluded_count,
            review_count=job.review_count,
            candidate_count=job.candidate_count,
            error_count=job.error_count
        )

    def _make_evidence(self, candidate_id: str, e_type: str, result: Any) -> CandidateEvidence:
        import dataclasses
        payload = dataclasses.asdict(result) if dataclasses.is_dataclass(result) else str(result)
        return CandidateEvidence(
            evidence_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            evidence_type=e_type,
            evidence_payload=payload
        )
