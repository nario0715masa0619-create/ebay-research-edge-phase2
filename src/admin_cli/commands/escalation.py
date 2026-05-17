from typing import Optional
from ..models import CliExecutionContext, CliCommandResult
from ..services.escalation_ops_service import EscalationOpsService

class EscalationCommands:
    def __init__(self, service: EscalationOpsService):
        self.service = service

    def active(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_active()
        return CliCommandResult(command_path="escalation active", records=records)

    def recent(self, context: CliExecutionContext, limit: int = 50) -> CliCommandResult:
        records = self.service.list_recent(limit=limit)
        return CliCommandResult(command_path="escalation recent", records=records)

    def show(self, context: CliExecutionContext, state_id: str) -> CliCommandResult:
        item = self.service.get_details(state_id)
        if not item:
            return CliCommandResult(command_path="escalation show", status="error", errors=[f"State ID {state_id} not found."], exit_code=2)
        return CliCommandResult(command_path="escalation show", records=[item])

    def ack(self, context: CliExecutionContext, state_id: str, note: str = None) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation ack", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
        
        if context.dry_run:
            return CliCommandResult(command_path="escalation ack", meta={"dry_run": True, "action": "acknowledge", "state_id": state_id})
            
        res = self.service.ack(state_id, "cli_user", note)
        return CliCommandResult(command_path="escalation ack", status=res.get("status", "success"), meta=res)

    def resolve(self, context: CliExecutionContext, state_id: str, note: str = None) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation resolve", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
            
        if context.dry_run:
            return CliCommandResult(command_path="escalation resolve", meta={"dry_run": True, "action": "resolve", "state_id": state_id})
            
        res = self.service.resolve(state_id, "cli_user", note)
        return CliCommandResult(command_path="escalation resolve", status=res.get("status", "success"), meta=res)

    def silence(self, context: CliExecutionContext, state_id: str, hours: int = 24, note: str = None) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation silence", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
            
        if context.dry_run:
            return CliCommandResult(command_path="escalation silence", meta={"dry_run": True, "action": "silence", "state_id": state_id, "hours": hours})
            
        res = self.service.silence(state_id, hours, "cli_user", note)
        return CliCommandResult(command_path="escalation silence", status=res.get("status", "success"), meta=res)

    def unsilence(self, context: CliExecutionContext, state_id: str, note: str = None) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation unsilence", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
            
        if context.dry_run:
            return CliCommandResult(command_path="escalation unsilence", meta={"dry_run": True, "action": "unsilence", "state_id": state_id})
            
        res = self.service.unsilence(state_id, "cli_user", note)
        return CliCommandResult(command_path="escalation unsilence", status=res.get("status", "success"), meta=res)

    def stats(self, context: CliExecutionContext) -> CliCommandResult:
        res = self.service.stats()
        return CliCommandResult(command_path="escalation stats", meta=res)

    def policies(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_policies()
        return CliCommandResult(command_path="escalation policies", records=records)

    # --- v0.2 Extensions ---
    def breached(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_breached()
        return CliCommandResult(command_path="escalation breached", records=records)

    def aging(self, context: CliExecutionContext, bucket: str) -> CliCommandResult:
        records = self.service.list_aging(bucket)
        return CliCommandResult(command_path="escalation aging", records=records)

    def timeline(self, context: CliExecutionContext, state_id: str) -> CliCommandResult:
        records = self.service.timeline(state_id)
        return CliCommandResult(command_path=f"escalation timeline {state_id}", records=records)

    def list_notes(self, context: CliExecutionContext, state_id: str) -> CliCommandResult:
        records = self.service.list_notes(state_id)
        return CliCommandResult(command_path=f"escalation notes list {state_id}", records=records)

    def add_note(self, context: CliExecutionContext, state_id: str, body: str) -> CliCommandResult:
        res = self.service.add_note(state_id, body, "cli_user")
        return CliCommandResult(command_path="escalation notes add", meta=res)

    def bulk_ack(self, context: CliExecutionContext, state_ids_str: str) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation bulk-ack", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
        state_ids = [s.strip() for s in state_ids_str.split(",") if s.strip()]
        if context.dry_run:
            return CliCommandResult(command_path="escalation bulk-ack", meta={"dry_run": True, "action": "bulk_ack", "count": len(state_ids)})
        res = self.service.bulk_ack(state_ids, "cli_user")
        return CliCommandResult(command_path="escalation bulk-ack", meta=res)

    def bulk_resolve(self, context: CliExecutionContext, state_ids_str: str) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation bulk-resolve", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
        state_ids = [s.strip() for s in state_ids_str.split(",") if s.strip()]
        if context.dry_run:
            return CliCommandResult(command_path="escalation bulk-resolve", meta={"dry_run": True, "action": "bulk_resolve", "count": len(state_ids)})
        res = self.service.bulk_resolve(state_ids, "cli_user")
        return CliCommandResult(command_path="escalation bulk-resolve", meta=res)

    def bulk_silence(self, context: CliExecutionContext, state_ids_str: str, hours: int) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation bulk-silence", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
        state_ids = [s.strip() for s in state_ids_str.split(",") if s.strip()]
        if context.dry_run:
            return CliCommandResult(command_path="escalation bulk-silence", meta={"dry_run": True, "action": "bulk_silence", "count": len(state_ids), "hours": hours})
        res = self.service.bulk_silence(state_ids, hours, "cli_user")
        return CliCommandResult(command_path="escalation bulk-silence", meta=res)

    def maintenance_list(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.maintenance_list()
        return CliCommandResult(command_path="escalation maintenance list", records=records)

    def maintenance_add(self, context: CliExecutionContext, starts: str, ends: str, action: str, seller: Optional[str], env: Optional[str], event: Optional[str]) -> CliCommandResult:
        from datetime import datetime
        starts_dt = datetime.fromisoformat(starts)
        ends_dt = datetime.fromisoformat(ends)
        res = self.service.maintenance_add(starts_dt, ends_dt, action, seller, env, event)
        return CliCommandResult(command_path="escalation maintenance add", meta=res)

    def maintenance_remove(self, context: CliExecutionContext, window_id: str) -> CliCommandResult:
        if not context.confirm and not context.dry_run:
            return CliCommandResult(command_path="escalation maintenance remove", status="error", errors=["Safety Guard: Use --confirm or --dry-run."], exit_code=6)
        if context.dry_run:
            return CliCommandResult(command_path="escalation maintenance remove", meta={"dry_run": True, "action": "remove_maintenance", "window_id": window_id})
        res = self.service.maintenance_remove(window_id)
        return CliCommandResult(command_path="escalation maintenance remove", meta=res)
