import argparse
import logging
from typing import List, Dict, Any
from src.admin_cli.models import CliExecutionContext, CliCommandResult
from src.admin_cli.services.seller_ops_service import SellerOpsService
from src.admin_cli.services.seller_doctor_service import SellerDoctorService
from src.admin_cli.services.seller_snapshot_ops_service import SellerSnapshotOpsService

logger = logging.getLogger(__name__)

class SellerCommands:
    def __init__(self, seller_ops: SellerOpsService, seller_doctor: SellerDoctorService, snapshot_ops: SellerSnapshotOpsService):
        self.seller_ops = seller_ops
        self.seller_doctor = seller_doctor
        self.snapshot_ops = snapshot_ops

    def list_sellers(self, context: CliExecutionContext) -> CliCommandResult:
        sellers = self.seller_ops.list_sellers()
        return CliCommandResult(
            command_path=context.command_path,
            records=sellers,
            message=f"Found {len(sellers)} sellers."
        )

    def list_environments(self, context: CliExecutionContext) -> CliCommandResult:
        envs = self.seller_ops.list_environments()
        return CliCommandResult(
            command_path=context.command_path,
            records=envs,
            message=f"Found {len(envs)} environments."
        )

    def list_bindings(self, context: CliExecutionContext, seller_account_id: str = None) -> CliCommandResult:
        bindings = self.seller_ops.list_bindings(seller_account_id)
        return CliCommandResult(
            command_path=context.command_path,
            records=bindings,
            message=f"Found {len(bindings)} bindings."
        )

    def activate_binding(self, context: CliExecutionContext, seller_account_id: str, environment_id: str) -> CliCommandResult:
        if not context.confirm:
            return CliCommandResult(
                command_path=context.command_path,
                status="confirmation_required",
                message=f"Are you sure you want to activate environment '{environment_id}' for seller '{seller_account_id}'?",
                exit_code=6
            )
        
        self.seller_ops.activate_binding(seller_account_id, environment_id)
        return CliCommandResult(
            command_path=context.command_path,
            message=f"Activated environment '{environment_id}' for seller '{seller_account_id}'."
        )

    def doctor_seller(self, context: CliExecutionContext, seller_account_id: str) -> CliCommandResult:
        report = self.seller_doctor.diagnose_seller(seller_account_id)
        return CliCommandResult(
            command_path=context.command_path,
            status="success" if report["status"] == "ok" else "error",
            records=report["checks"],
            summary={"status": report["status"]},
            message=f"Doctor report for seller '{seller_account_id}'."
        )

    def show_policies(self, context: CliExecutionContext, seller_account_id: str, marketplace_id: str) -> CliCommandResult:
        policies = self.snapshot_ops.get_latest_policies(seller_account_id, marketplace_id)
        if not policies:
            return CliCommandResult(command_path=context.command_path, status="error", message="No policy snapshot found.")
        
        return CliCommandResult(
            command_path=context.command_path,
            records=[policies],
            message=f"Latest policy snapshot for {seller_account_id} on {marketplace_id}."
        )

    def show_locations(self, context: CliExecutionContext, seller_account_id: str, location_key: str) -> CliCommandResult:
        locations = self.snapshot_ops.get_latest_locations(seller_account_id, location_key)
        if not locations:
            return CliCommandResult(command_path=context.command_path, status="error", message="No location snapshot found.")
        
        return CliCommandResult(
            command_path=context.command_path,
            records=[locations],
            message=f"Latest location snapshot for {seller_account_id} - {location_key}."
        )
