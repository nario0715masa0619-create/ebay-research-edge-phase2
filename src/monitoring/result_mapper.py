import uuid
from datetime import datetime
from typing import Dict, Any, List
from src.ebay.models import ProductCandidate, EbayListing, MonitoringEvent
from .old_models import MonitoringReviseResult

class MonitoringResultMapper:
    def update_candidate(self, candidate: ProductCandidate, latest_source: Dict[str, Any], profit_res: Dict[str, Any]):
        candidate.source_price_jpy = latest_source.get("latest_source_price_jpy", candidate.source_price_jpy)
        candidate.source_shipping_jpy = latest_source.get("latest_source_shipping_jpy", candidate.source_shipping_jpy)
        candidate.source_stock_status = latest_source.get("latest_source_stock_status", candidate.source_stock_status)
        
        candidate.expected_profit_jpy = profit_res.get("updated_expected_profit_jpy", candidate.expected_profit_jpy)
        candidate.expected_profit_rate = profit_res.get("updated_expected_profit_rate", candidate.expected_profit_rate)
        candidate.standard_score = profit_res.get("updated_standard_score", candidate.standard_score)
        
        candidate.last_checked_at = datetime.now()
        candidate.updated_at = datetime.now()

    def update_listing(self, listing: EbayListing, res: MonitoringReviseResult):
        if res.revise_status == "updated":
            # In real logic, update price/quantity if they were in the result
            pass
        
        listing.updated_at = datetime.now()
        if res.error_summary:
            listing.last_revise_error = res.error_summary

    def create_events(self, candidate_id: str, sku: str, 
                      source_state: Dict[str, Any], 
                      revise_action: str) -> List[MonitoringEvent]:
        events = []
        # Simplified event creation
        if source_state.get("latest_source_stock_status") == "out_of_stock":
            events.append(MonitoringEvent(
                event_id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                sku=sku,
                event_scope="source",
                event_type="stock_change",
                before_value="in_stock",
                after_value="out_of_stock",
                action_taken=revise_action
            ))
        return events
