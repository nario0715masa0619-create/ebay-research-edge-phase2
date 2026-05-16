from typing import Dict, Any, List
from src.ebay.models import ProductCandidate
from .models import ListingSyncRequest

class RecoveryDecisionEngine:
    def decide(self, request: ListingSyncRequest, candidate: ProductCandidate, comparison: Dict[str, Any], remote_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decides on the recovery action based on drifts and policy.
        """
        drifts = comparison["drifts"]
        action = "keep_db_and_mark_synced"
        reason_codes = []
        review_required = False
        recoverable = True

        if not drifts:
            return {
                "action": "keep_db_and_mark_synced",
                "reason_codes": ["no_drift"],
                "review_required": False
            }

        # Priority 1: Critical Missing Links
        if "offer_missing_remote" in drifts:
            # If DB says listed but remote has nothing, it's a critical drift
            if candidate.status == "listed":
                action = "mark_review_required"
                reason_codes.append("remote_offer_not_found_while_listed")
                review_required = True
                recoverable = False
            else:
                action = "keep_db_and_mark_synced" # Might be just not published yet

        elif "missing_ebay_listing_row" in drifts or "missing_listing_id_in_db" in drifts or "missing_offer_id_in_db" in drifts:
            if request.allow_repair_db_state:
                action = "repair_db_ids_only"
                reason_codes.append("repairing_db_linkage")
            else:
                action = "mark_review_required"
                review_required = True

        elif "db_marked_listed_but_remote_unpublished" in drifts:
            # Check if we should try to publish or just review
            action = "mark_review_required"
            reason_codes.append("remote_unpublished_unexpectedly")
            review_required = True

        elif "db_marked_active_but_remote_zero_quantity" in drifts:
            if request.allow_zero_quantity_reconcile:
                action = "repair_db_status_only"
                reason_codes.append("reconciling_zero_quantity_to_paused")
            else:
                action = "mark_review_required"
                review_required = True

        elif "price_drift" in drifts or "quantity_drift" in drifts:
            if request.allow_recover_inventory:
                action = "reconcile_remote_from_db" 
                reason_codes.append("syncing_remote_to_db_baseline")
            else:
                action = "reconcile_db_from_remote" 
                reason_codes.append("syncing_db_to_remote_reality")

        elif "listing_status_drift" in drifts or "offer_status_drift" in drifts:
            action = "repair_db_status_only"
            reason_codes.append("syncing_db_status_to_remote")

        return {
            "action": action,
            "reason_codes": reason_codes,
            "review_required": review_required,
            "recoverable": recoverable
        }

        return {
            "action": action,
            "reason_codes": reason_codes,
            "review_required": review_required,
            "recoverable": recoverable
        }
