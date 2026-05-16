from ..models import CliExecutionContext, CliCommandResult

class ListingCommands:
    def __init__(self, listing_service):
        self.service = listing_service

    def list(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_listings(limit=context.limit or 20)
        return CliCommandResult(command_path="listings list", records=records)

    def sync(self, context: CliExecutionContext, sku: str) -> CliCommandResult:
        return self.service.sync_listing(sku, dry_run=context.dry_run, force_recheck=context.force_recheck)

    def withdraw(self, context: CliExecutionContext, sku: str) -> CliCommandResult:
        if not context.confirm:
            return CliCommandResult(
                command_path="listings withdraw", 
                status="confirmation_required", 
                message=f"Withdraw listing for SKU {sku}? Use --confirm to proceed.",
                exit_code=6
            )
        # Assuming listing_service has withdraw_listing
        if hasattr(self.service, "withdraw_listing"):
            return self.service.withdraw_listing(sku, dry_run=context.dry_run)
        return CliCommandResult(command_path="listings withdraw", status="error", errors=["Not implemented"], exit_code=5)
