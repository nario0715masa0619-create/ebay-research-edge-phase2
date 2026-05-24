from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ExecutionPayload(BaseModel):
    """
    Schema for the execution payload handed off to the listing execution layer.
    """
    # Required Fields
    listing_id: str = Field(..., description="Unique ID for the listing execution (can be candidate_id or specific execution ID)")
    seller: str = Field(..., description="Seller account ID")
    sku: str = Field(..., description="SKU of the product")
    bundle_state: str = Field(..., description="Bundle configuration state")
    market_eval: Dict[str, Any] = Field(..., description="Market evaluation results dictionary")
    profitability_score: float = Field(..., description="Calculated profitability score")
    
    # Context Fields
    environment: str = Field(..., description="Target environment (e.g., sandbox, production)")
    dry_run: bool = Field(False, description="If True, execution is simulated")
    attempt_id: str = Field(..., description="Unique attempt ID for idempotency")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Payload generation timestamp")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize payload to dict"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionPayload':
        """Deserialize payload from dict"""
        return cls(**data)

    @classmethod
    def from_listing(
        cls, 
        candidate_data: Dict[str, Any], 
        handoff_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> 'ExecutionPayload':
        """
        Factory method to create an ExecutionPayload from upstream domain models.
        In a real application, candidate_data and handoff_data might be actual Domain Objects.
        Here we use Dicts to decouple dependencies while demonstrating the factory logic.
        """
        return cls(
            listing_id=handoff_data.get('handoff_id', ''),
            seller=candidate_data.get('seller_account_id', ''),
            sku=candidate_data.get('sku', ''),
            bundle_state=candidate_data.get('bundle_signature', 'none'),
            market_eval=candidate_data.get('market_eval', {}),
            profitability_score=candidate_data.get('profitability_score', 0.0),
            environment=context.get('environment', 'sandbox'),
            dry_run=context.get('dry_run', False),
            attempt_id=context.get('attempt_id', ''),
            timestamp=context.get('timestamp', datetime.now(timezone.utc))
        )
