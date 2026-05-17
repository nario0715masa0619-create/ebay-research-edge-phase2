import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.ebay.models import ProductCandidate, EbayListing, CandidateEvidence, MonitoringEvent
from src.ebay.api_client import EbayInventoryApiClient
from .models import ListingSyncRequest, ListingSyncResult, ListingSyncBatchResult
from .target_selector import SyncTargetSelector
from .state_fetcher import EbayStateFetcher
from .comparator import StateComparator
from .recovery_decision_engine import RecoveryDecisionEngine
from .offer_recovery_executor import OfferRecoveryExecutor
from .inventory_recovery_executor import InventoryRecoveryExecutor
from .result_mapper import SyncResultMapper
from .retry_classifier import SyncRetryClassifier

logger = logging.getLogger(__name__)

class ListingSyncRecoveryGateway:
    def __init__(self, candidate_repo, evidence_repo, job_repo, listing_repo, event_repo=None, api_client=None, notification_dispatcher=None):
        self.candidate_repo = candidate_repo
        self.evidence_repo = evidence_repo
        self.job_repo = job_repo
        self.listing_repo = listing_repo
        self.event_repo = event_repo
        self.notification_dispatcher = notification_dispatcher
        
        self.api_client = api_client or EbayInventoryApiClient({})
        
        self.target_selector = SyncTargetSelector()
        self.state_fetcher = EbayStateFetcher(self.api_client)
        self.comparator = StateComparator()
        self.decision_engine = RecoveryDecisionEngine()
        self.offer_executor = OfferRecoveryExecutor(self.api_client)
        self.inv_executor = InventoryRecoveryExecutor(self.api_client)
        self.mapper = SyncResultMapper()
        self.retry_classifier = SyncRetryClassifier()

    def sync_and_recover_listing(self, request: ListingSyncRequest) -> ListingSyncResult:
        candidate = self.candidate_repo.get_by_candidate_id(request.candidate_id)
        listing = self.listing_repo.get_by_candidate_id(request.candidate_id)
        
        if not candidate:
            return ListingSyncResult(candidate_id=request.candidate_id, sku=request.sku, sync_status="failed", error_summary="Candidate not found")

        # 1. Target Selector
        if not self.target_selector.evaluate(candidate, listing, request.force_recheck):
            return ListingSyncResult(candidate_id=request.candidate_id, sku=request.sku, sync_status="skipped")

        res = ListingSyncResult(candidate_id=request.candidate_id, sku=request.sku, sync_status="running")
        
        # 2. Fetch Remote State
        remote_state = self.state_fetcher.fetch_remote_state(request.sku, request.offer_id or (listing.offer_id if listing else None))
        self._save_evidence(candidate.candidate_id, "listing_remote_state", remote_state)
        
        # If we have errors that are NOT 404, or if we have no state at all and it was a real API error
        real_errors = [e for e in remote_state["errors"] if "404" not in e]
        if real_errors and not remote_state["offer"] and not remote_state["inventory_item"]:
            res.sync_status = "failed"
            res.error_summary = "; ".join(remote_state["errors"])
            return res

        # 3. Compare State
        comparison = self.comparator.compare(candidate, listing, remote_state)
        res.detected_drift_types = comparison["drifts"]
        res.ebay_offer_found = comparison["remote_offer_found"]
        res.ebay_inventory_found = comparison["remote_inventory_found"]
        self._save_evidence(candidate.candidate_id, "listing_state_comparison", comparison)

        # 4. Decide Action
        decision = self.decision_engine.decide(request, candidate, comparison, remote_state)
        res.recovery_action = decision["action"]
        res.review_required_flag = decision["review_required"]
        self._save_evidence(candidate.candidate_id, "listing_recovery_decision", decision)

        if request.dry_run:
            res.sync_status = "synced" if not comparison["drifts"] else "drift_detected"
            res.success_flag = True
            return res

        # 5. Execution
        event_type = "listing_sync_completed"
        action_taken = "keep"

        if decision["action"] == "repair_db_ids_only":
            if not listing:
                listing = EbayListing(
                    candidate_id=candidate.candidate_id, 
                    sku=candidate.sku, 
                    marketplace_id=request.marketplace_id,
                    listing_price_usd=0, 
                    quantity=0
                )
            self.mapper.update_listing_from_remote(listing, remote_state["offer"])
            if not request.dry_run:
                self.listing_repo.upsert(listing)
            res.sync_status = "repaired"
            res.recovery_applied_flag = True
            event_type = "listing_db_repaired"
            action_taken = "repair_ids"

        elif decision["action"] == "repair_db_status_only":
            if listing:
                self.mapper.update_listing_from_remote(listing, remote_state["offer"])
                if not request.dry_run:
                    self.listing_repo.upsert(listing)
            self.mapper.update_candidate_from_sync(candidate, "repaired", False, remote_state["offer"])
            if not request.dry_run:
                self.candidate_repo.upsert(candidate)
            res.sync_status = "repaired"
            res.recovery_applied_flag = True
            event_type = "listing_db_repaired"
            action_taken = "repair_status"

        elif decision["action"] == "reconcile_remote_from_db" and listing:
            offer_id = remote_state["offer"]["offerId"]
            rec_res = self.inv_executor.execute_price_qty_sync(candidate.sku, offer_id, listing.listing_price_usd, listing.quantity, dry_run=request.dry_run)
            self._save_evidence(candidate.candidate_id, "listing_recovery_execution", rec_res)
            if rec_res.get("success"):
                res.sync_status = "repaired"
                res.recovery_applied_flag = True
                event_type = "listing_remote_reconciled"
                action_taken = "reconcile_remote"
            else:
                res.sync_status = "failed"
                res.error_summary = str(rec_res)

        elif decision["action"] == "keep_db_and_mark_synced":
            if listing and remote_state["offer"]:
                self.mapper.update_listing_from_remote(listing, remote_state["offer"])
                if not request.dry_run:
                    self.listing_repo.upsert(listing)
            res.sync_status = "synced"

        # 6. Finalize
        if res.review_required_flag:
            self.mapper.update_candidate_from_sync(candidate, res.sync_status, True)
            if not request.dry_run:
                self.candidate_repo.upsert(candidate)
            event_type = "listing_sync_review_required"
            action_taken = "review"

        # Log Monitoring Event
        if self.event_repo and not request.dry_run:
            event = MonitoringEvent(
                event_id=str(uuid.uuid4()),
                candidate_id=candidate.candidate_id,
                sku=candidate.sku,
                event_scope="marketplace",
                event_type=event_type,
                before_value="unknown",
                after_value=res.sync_status,
                action_taken=action_taken
            )
            self.event_repo.save(event)

        res.success_flag = (res.sync_status in ["synced", "repaired"])
        
        # 7. Notify if needed
        self._notify_if_needed(res, candidate, request.dry_run)
        
        return res

    def _notify_if_needed(self, res: ListingSyncResult, candidate, dry_run: bool):
        if not self.notification_dispatcher:
            return
            
        from src.notification.models import NotificationEvent
        
        if res.review_required_flag:
            event = NotificationEvent(
                event_type="listing_sync_review_required",
                source_layer="listing_sync",
                sku=res.sku,
                candidate_id=res.candidate_id,
                title=f"Manual Review Required for Sync: {res.sku}",
                summary=f"Drift detected: {', '.join(res.detected_drift_types)}",
                severity="warning",
                priority="normal",
                review_required_flag=True
            )
            self.notification_dispatcher.notify(event, dry_run=dry_run)
        
        elif res.sync_status == "drift_detected" or (res.detected_drift_types and res.sync_status != "repaired"):
            event = NotificationEvent(
                event_type="listing_drift_detected",
                source_layer="listing_sync",
                sku=res.sku,
                candidate_id=res.candidate_id,
                title=f"Listing Drift Detected: {res.sku}",
                summary=f"Types: {', '.join(res.detected_drift_types)}",
                severity="warning",
                priority="normal"
            )
            self.notification_dispatcher.notify(event, dry_run=dry_run)
        
        elif res.sync_status == "failed":
            event = NotificationEvent(
                event_type="listing_recovery_failed",
                source_layer="listing_sync",
                sku=res.sku,
                candidate_id=res.candidate_id,
                title=f"Recovery Failed: {res.sku}",
                summary=res.error_summary,
                severity="error",
                priority="high"
            )
            self.notification_dispatcher.notify(event, dry_run=dry_run)

    def _save_evidence(self, candidate_id: str, e_type: str, payload: dict):
        evidence = CandidateEvidence(
            evidence_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            evidence_type=e_type,
            evidence_payload=payload
        )
        self.evidence_repo.save(evidence)

    def run_listing_sync_recovery_gateway(self, candidate_ids: List[str] = None, limit: int = None, dry_run: bool = False, force_recheck: bool = False) -> ListingSyncBatchResult:
        job = self.job_repo.start_run("listing_sync_recovery_gateway")
        batch_res = ListingSyncBatchResult(run_id=job.run_id)
        
        if not candidate_ids:
            # Simplified: pick listed/approved candidates
            candidates = self.candidate_repo.list_all(limit=limit) # This is a placeholder, should use smarter selection
            candidate_ids = [c.candidate_id for c in candidates]

        for cid in candidate_ids:
            cand = self.candidate_repo.get_by_candidate_id(cid)
            if not cand: continue
            
            req = ListingSyncRequest(candidate_id=cid, sku=cand.sku, run_id=job.run_id, dry_run=dry_run, force_recheck=force_recheck)
            res = self.sync_and_recover_listing(req)
            
            batch_res.processed_count += 1
            if res.sync_status == "synced":
                batch_res.synced_count += 1
            elif res.sync_status == "repaired":
                batch_res.repaired_count += 1
            elif res.sync_status == "skipped":
                batch_res.skipped_count += 1
            elif res.review_required_flag:
                batch_res.review_count += 1
            elif not res.success_flag:
                batch_res.fatal_error_count += 1
            else:
                batch_res.unchanged_count += 1
                
        self.job_repo.finish_run(job.run_id, "completed", batch_res.__dict__)
        return batch_res
