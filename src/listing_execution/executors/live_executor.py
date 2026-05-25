from typing import Dict, Any, List
from datetime import datetime, timezone
from src.listing_execution.gateways.execution_gateway import ExecutionGateway, ExecutionResult, ValidationResult
from src.listing_execution.models.execution_payload import ExecutionPayload
from src.listing_execution.gateways.ebay_api_gateway import EBayApiGateway, RateLimitError, InvalidRequestError, TimeoutError

class LiveExecutor(ExecutionGateway):
    """
    Live executor that talks to the actual marketplace API.
    In Wave 1, this uses the mock EBayApiGateway to simulate API interaction.
    """
    def __init__(
        self, 
        allowed_environments: List[str], 
        allowed_sellers: List[str],
        api_gateway: EBayApiGateway
    ):
        self.allowed_environments = allowed_environments
        self.allowed_sellers = allowed_sellers
        self.api_gateway = api_gateway

    def supports_environment(self, environment: str) -> bool:
        return environment in self.allowed_environments
        
    def validate(self, payload: ExecutionPayload, credentials: Dict[str, Any] = None) -> ValidationResult:
        if payload.environment not in self.allowed_environments:
            return ValidationResult(
                is_valid=False,
                error_messages=[f"Environment '{payload.environment}' is not supported by LiveExecutor."]
            )
            
        if payload.seller not in self.allowed_sellers:
            return ValidationResult(
                is_valid=False,
                error_messages=[f"Seller '{payload.seller}' is not supported by LiveExecutor."]
            )
            
        if credentials is not None and not self.api_gateway.validate_credentials(credentials):
            return ValidationResult(
                is_valid=False,
                error_messages=["Invalid credentials provided."]
            )
            
        return ValidationResult(is_valid=True, error_messages=[])

    def execute(self, payload: ExecutionPayload, credentials: Dict[str, Any] = None) -> ExecutionResult:
        # Validate first
        val_result = self.validate(payload, credentials)
        if not val_result.is_valid:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason=", ".join(val_result.error_messages),
                executed_at=datetime.now(timezone.utc)
            )

        # Handle dry run
        if payload.dry_run:
            return ExecutionResult(
                status="success",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason="Dry run successful (simulated).",
                executed_at=datetime.now(timezone.utc)
            )

        if not credentials:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason="Missing credentials for live execution.",
                executed_at=datetime.now(timezone.utc)
            )

        try:
            # Step 1: Create or Replace Inventory Item
            self.api_gateway.create_or_replace_inventory_item(
                sku=payload.sku, 
                payload=payload.to_dict(), 
                credentials=credentials
            )
            
            # Step 2: Create Offer
            offer_id = self.api_gateway.create_offer(
                sku=payload.sku,
                marketplace_id="EBAY_US",
                credentials=credentials
            )
            
            # Step 3: Publish Offer
            response = self.api_gateway.publish_offer(
                offer_id=offer_id,
                credentials=credentials
            )
            
            return ExecutionResult(
                status="success",
                listing_id=response.listing_id,
                attempt_id=payload.attempt_id,
                executed_at=response.timestamp or datetime.now(timezone.utc)
            )
            
        except TimeoutError as e:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason=f"Timeout: {str(e)}",
                executed_at=datetime.now(timezone.utc)
            )
        except RateLimitError as e:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason=f"Rate Limit: {str(e)}",
                executed_at=datetime.now(timezone.utc)
            )
        except InvalidRequestError as e:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason=f"Invalid Request: {str(e)}",
                executed_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            return ExecutionResult(
                status="failed",
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                error_reason=f"Unknown Error: {str(e)}",
                executed_at=datetime.now(timezone.utc)
            )
