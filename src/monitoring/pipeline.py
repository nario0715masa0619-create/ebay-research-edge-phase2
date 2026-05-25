import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.ebay.models import ProductCandidate, EbayListing, CandidateEvidence, MonitoringEvent
from src.ebay.api_client import EbayInventoryApiClient
from .old_models import MonitoringReviseRequest, MonitoringReviseResult, MonitoringReviseBatchResult
from .source_refresher import SourceStateRefresher
from .target_selector import MonitoringTargetSelector
from .marketplace_sync import MarketplaceStateSync
from .profit_recalculator import ProfitRecalculator
from .revise_decision_engine import ReviseDecisionEngine
from .revise_executor import PriceQuantityReviseExecutor
from .withdraw_executor import WithdrawExecutor
from .result_mapper import MonitoringResultMapper
from .retry_classifier import ReviseRetryClassifier

class MonitoringRevisePipeline:
    def __init__(self, candidate_repo, evidence_repo, job_repo, listing_repo, event_repo=None, api_client=None):
        self.candidate_repo = candidate_repo
        self.evidence_repo = evidence_repo
        self.job_repo = job_repo
        self.listing_repo = listing_repo
        self.event_repo = event_repo
        
        self.api_client = api_client or EbayInventoryApiClient({})
        self.target_selector = MonitoringTargetSelector()
        self.source_refresher = SourceStateRefresher()
        self.marketplace_sync = MarketplaceStateSync(self.api_client)
        self.profit_recalculator = ProfitRecalculator()
        self.decision_engine = ReviseDecisionEngine()
        self.revise_executor = PriceQuantityReviseExecutor(self.api_client)
        self.withdraw_executor = WithdrawExecutor(self.api_client)
        self.mapper = MonitoringResultMapper()
        self.retry_classifier = ReviseRetryClassifier()

    def monitor_and_revise_listing(self, request: MonitoringReviseRequest) -> MonitoringReviseResult:
        candidate = self.candidate_repo.get_by_candidate_id(request.candidate_id)
        listing = self.listing_repo.get_by_candidate_id(request.candidate_id)
        
        if not candidate or not listing:
            return MonitoringReviseResult(candidate_id=request.candidate_id, sku="unknown", monitoring_status="failed", error_summary="Candidate or Listing not found")

        # 2. Target Selector / Guard
        sel_res = self.target_selector.evaluate(candidate)
        if not sel_res.eligible_flag:
            return MonitoringReviseResult(
                candidate_id=candidate.candidate_id, 
                sku=candidate.sku, 
                monitoring_status="skipped", 
                monitoring_reason_codes=sel_res.selector_reason_codes,
                error_summary="Target selector excluded"
            )

        res = MonitoringReviseResult(candidate_id=candidate.candidate_id, sku=candidate.sku, monitoring_status="running")
        
        # 2. Source State Refresh
        source_res = self.source_refresher.refresh(candidate)
        res.source_state_status = source_res["source_state_status"]
        self._save_evidence(candidate.candidate_id, "source_state_refresh", source_res)
        
        # 3. Marketplace State Sync
        market_res = self.marketplace_sync.sync(listing.offer_id)
        res.marketplace_state_status = market_res["marketplace_state_status"]
        self._save_evidence(candidate.candidate_id, "marketplace_state_sync", market_res)
        
        # 5. Profit Recalculation
        profit_res = self.profit_recalculator.recalculate(candidate, source_res)
        res.profit_recalculation_status = profit_res["profit_recalculation_status"]
        self._save_evidence(candidate.candidate_id, "profit_recalculation", profit_res)
        
        # 6. Revise Decision
        decision = self.decision_engine.decide(source_res, market_res, profit_res, request.strictness)
        res.revise_action = decision["revise_action"]
        res.monitoring_reason_codes = decision["decision_reason_codes"]
        res.review_required_flag = decision["review_required_flag"]
        self._save_evidence(candidate.candidate_id, "revise_decision", decision)
        
        if request.dry_run:
            res.monitoring_status = "skipped"
            res.success_flag = True
            return res

        # 7/8. Execute Revise or Withdraw
        if res.revise_action in ["revise_price", "revise_quantity", "revise_price_quantity", "set_quantity_zero"]:
            # Simplified: quantity zero handling
            target_quantity = 0 if res.revise_action == "set_quantity_zero" else 1
            rev_res = self.revise_executor.execute(candidate.sku, listing.offer_id, None, target_quantity)
            res.revise_status = rev_res["revise_status"]
            self._save_evidence(candidate.candidate_id, "revise_execution", rev_res)
            if not rev_res["success"]:
                return self._handle_failure(candidate, res, rev_res)
                
        elif res.revise_action == "withdraw_offer":
            wit_res = self.withdraw_executor.execute(listing.offer_id)
            res.withdraw_status = wit_res["withdraw_status"]
            self._save_evidence(candidate.candidate_id, "withdraw_execution", wit_res)
            if not wit_res["success"]:
                return self._handle_failure(candidate, res, wit_res)

        # 9. Result Mapping
        res.monitoring_status = self._map_action_to_status(res.revise_action)
        res.success_flag = True
        
        self.mapper.update_candidate(candidate, source_res, profit_res)
        self.mapper.update_listing(listing, res)
        events = self.mapper.create_events(candidate.candidate_id, candidate.sku, source_res, res.revise_action)
        
        # Persist
        self.candidate_repo.upsert(candidate)
        self.listing_repo.upsert(listing)
        if self.event_repo:
            for e in events:
                self.event_repo.save(e)
        
        return res

    def _handle_failure(self, candidate, res, error_res) -> MonitoringReviseResult:
        res.monitoring_status = "failed"
        res.error_summary = error_res.get("error_summary") or str(error_res.get("response_payload"))
        
        classification, is_retryable, is_review = self.retry_classifier.classify(error_res)
        res.retryable_flag = is_retryable
        res.review_required_flag = is_review
        res.monitoring_status = classification
        
        return res

    def _map_action_to_status(self, action: str) -> str:
        mapping = {
            "keep": "kept",
            "revise_price": "revised",
            "revise_quantity": "revised",
            "revise_price_quantity": "revised",
            "set_quantity_zero": "quantity_zeroed",
            "withdraw_offer": "withdrawn",
            "review_required": "review_required"
        }
        return mapping.get(action, "running")

    def _save_evidence(self, candidate_id: str, e_type: str, payload: dict):
        evidence = CandidateEvidence(
            evidence_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            evidence_type=e_type,
            evidence_payload=payload,
            rule_version="v1"
        )
        self.evidence_repo.save(evidence)

    def run_monitoring_revise_pipeline(self, candidate_ids: List[str] = None, limit: int = None, dry_run: bool = False) -> MonitoringReviseBatchResult:
        job = self.job_repo.start_run("monitoring_revise_pipeline")
        batch_res = MonitoringReviseBatchResult(run_id=job.run_id)
        
        if not candidate_ids:
            # Pick listed candidates
            candidates = self.candidate_repo.list_by_status("listed", limit=limit)
            candidate_ids = [c.candidate_id for c in candidates]

        for cid in candidate_ids:
            req = MonitoringReviseRequest(candidate_id=cid, run_id=job.run_id, dry_run=dry_run)
            res = self.monitor_and_revise_listing(req)
            
            batch_res.processed_count += 1
            if res.monitoring_status == "kept":
                batch_res.keep_count += 1
            elif res.monitoring_status == "revised":
                batch_res.revised_count += 1
            elif res.monitoring_status == "quantity_zeroed":
                batch_res.zeroed_count += 1
            elif res.monitoring_status == "withdrawn":
                batch_res.withdrawn_count += 1
            elif res.monitoring_status == "review_required":
                batch_res.review_count += 1
            elif res.monitoring_status == "retryable":
                batch_res.retryable_error_count += 1
            else:
                batch_res.fatal_error_count += 1
                
        self.job_repo.finish_run(job.run_id, "completed", batch_res.__dict__)
        return batch_res
