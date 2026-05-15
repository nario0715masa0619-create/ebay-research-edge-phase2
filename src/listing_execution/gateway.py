import uuid
from datetime import datetime
from typing import List, Optional
from src.ebay.models import ProductCandidate, CandidateEvidence
from src.ebay.api_client import EbayInventoryApiClient
from .models import ListingExecutionRequest, ListingExecutionResult, ListingExecutionBatchResult
from .guard import CandidateExecutionGuard
from .inventory_item_executor import InventoryItemExecutor
from .offer_executor import OfferExecutor
from .publish_executor import PublishExecutor
from .result_mapper import ExecutionResultMapper
from .retry_classifier import RetryClassifier

class ListingExecutionGateway:
    def __init__(self, candidate_repo, evidence_repo, job_repo, listing_repo):
        self.candidate_repo = candidate_repo
        self.evidence_repo = evidence_repo
        self.job_repo = job_repo
        self.listing_repo = listing_repo
        
        self.api_client = EbayInventoryApiClient()
        self.guard = CandidateExecutionGuard()
        self.inv_executor = InventoryItemExecutor(self.api_client)
        self.off_executor = OfferExecutor(self.api_client)
        self.pub_executor = PublishExecutor(self.api_client)
        self.mapper = ExecutionResultMapper()
        self.retry_classifier = RetryClassifier()

    def execute_listing_candidate(self, request: ListingExecutionRequest) -> ListingExecutionResult:
        candidate = self.candidate_repo.get_by_candidate_id(request.candidate_id)
        if not candidate:
            return ListingExecutionResult(candidate_id=request.candidate_id, sku="unknown", execution_status="failed", error_summary="Candidate not found")

        # 2. execution guard
        is_valid, blockers = self.guard.validate(candidate, request)
        if not is_valid:
            return ListingExecutionResult(
                candidate_id=candidate.candidate_id,
                sku=candidate.sku,
                execution_status="skipped",
                execution_reason_codes=blockers,
                error_summary="Guard failed"
            )

        if request.dry_run:
            return ListingExecutionResult(
                candidate_id=candidate.candidate_id,
                sku=candidate.sku,
                execution_status="skipped",
                execution_reason_codes=["dry_run_simulated"],
                success_flag=True
            )

        res = ListingExecutionResult(candidate_id=candidate.candidate_id, sku=candidate.sku, execution_status="running")
        
        # 4. createOrReplaceInventoryItem
        inv_res = self.inv_executor.execute(candidate.sku, candidate.inventory_item_draft_json)
        res.inventory_item_status = inv_res["status"]
        self._save_evidence(candidate.candidate_id, "inventory_item_execution", inv_res)
        
        if not inv_res["success"]:
            return self._handle_failure(candidate, res, inv_res)

        # 6. createOffer
        off_res = self.off_executor.execute(candidate.offer_draft_json)
        res.offer_status = off_res["status"]
        res.offer_id = off_res.get("offer_id")
        self._save_evidence(candidate.candidate_id, "offer_execution", off_res)
        
        if not off_res["success"]:
            return self._handle_failure(candidate, res, off_res)

        # 7. publishOffer
        pub_res = self.pub_executor.execute(res.offer_id)
        res.publish_status = pub_res["status"]
        res.listing_id = pub_res.get("listing_id")
        self._save_evidence(candidate.candidate_id, "publish_execution", pub_res)
        
        if not pub_res["success"]:
            return self._handle_failure(candidate, res, pub_res)

        # 8. Success
        res.execution_status = "succeeded"
        res.success_flag = True
        
        # 9. Update Repos
        listing = self.mapper.map_to_listing(candidate, res)
        self.listing_repo.upsert(listing)
        self.mapper.update_candidate(candidate, res)
        self.candidate_repo.upsert(candidate)
        
        return res

    def _handle_failure(self, candidate, res, error_res) -> ListingExecutionResult:
        res.execution_status = "failed"
        res.error_summary = error_res.get("error") or str(error_res.get("response"))
        
        classification, is_retryable, is_review = self.retry_classifier.classify(error_res)
        res.retryable_flag = is_retryable
        res.review_required_flag = is_review
        res.execution_status = classification
        
        # Update Candidate with error
        self.mapper.update_candidate(candidate, res)
        self.candidate_repo.upsert(candidate)
        
        return res

    def _save_evidence(self, candidate_id: str, e_type: str, payload: dict):
        evidence = CandidateEvidence(
            evidence_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            evidence_type=e_type,
            evidence_payload=payload,
            rule_version="v1"
        )
        self.evidence_repo.save(evidence)

    def run_listing_execution_gateway(self, candidate_ids: List[str] = None, limit: int = None, dry_run: bool = False) -> ListingExecutionBatchResult:
        job = self.job_repo.start_run("ebay_listing_execution_gateway")
        batch_res = ListingExecutionBatchResult(run_id=job.run_id)
        
        if not candidate_ids:
            # Pick candidates that are ready
            candidates = self.candidate_repo.list_by_status("approved", limit=limit)
            # Filter for listing_readiness_status == "ready"
            candidates = [c for c in candidates if c.listing_readiness_status == "ready"]
            candidate_ids = [c.candidate_id for c in candidates]

        for cid in candidate_ids:
            req = ListingExecutionRequest(candidate_id=cid, run_id=job.run_id, dry_run=dry_run)
            res = self.execute_listing_candidate(req)
            
            batch_res.processed_count += 1
            if res.execution_status == "succeeded":
                batch_res.success_count += 1
            elif res.execution_status == "skipped":
                batch_res.skipped_count += 1
            elif res.execution_status == "retryable":
                batch_res.retryable_error_count += 1
            elif res.execution_status == "review_required":
                batch_res.review_required_count += 1
            else:
                batch_res.fatal_error_count += 1
                
        self.job_repo.finish_run(job.run_id, "completed", batch_res.__dict__)
        return batch_res
