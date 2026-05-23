from ..models import CliExecutionContext, CliCommandResult
from src.admin_cli.services.discovery_review_ops_service import DiscoveryReviewOpsService
from src.discovery.market_seed_builder import MarketSeedBuilder
from src.discovery.models import CanonicalProductCandidate
from src.db.session import SessionManager
from src.db.models import CanonicalProductCandidateModel
from sqlalchemy import select

def _get_candidate_domain_model(candidate_id: str) -> CanonicalProductCandidate:
    manager = SessionManager()
    with manager.session() as session:
        r = session.execute(
            select(CanonicalProductCandidateModel).where(CanonicalProductCandidateModel.candidate_id == candidate_id)
        ).scalar_one_or_none()
        if not r:
            return None
        return CanonicalProductCandidate(
            candidate_id=r.candidate_id,
            canonical_title=r.canonical_title,
            canonical_brand=r.canonical_brand,
            canonical_model=r.canonical_model,
            canonical_mpn=r.canonical_mpn,
            canonical_gtins=r.canonical_gtins_json or [],
            variation_signature=r.variation_signature,
            bundle_signature=r.bundle_signature,
            ambiguity_flags=r.ambiguity_flags_json or [],
            review_required=r.review_required,
            category_candidates=r.category_candidates_json or [],
            feature_payload=r.feature_payload_json or {}
        )

class DiscoveryReviewCommands:
    def __init__(self, ops_service: DiscoveryReviewOpsService):
        self.ops = ops_service

    def list(self, context: CliExecutionContext) -> CliCommandResult:
        limit = context.limit or 50
        items = self.ops.list_pending_reviews(limit=limit)
        records = [
            {
                "candidate_id": i.candidate_id,
                "title": i.canonical_title,
                "sources": i.source_count,
                "ambiguity": i.ambiguity_severity
            } for i in items
        ]
        return CliCommandResult(command_path="discovery review list", records=records)

    def show(self, context: CliExecutionContext, candidate_id: str) -> CliCommandResult:
        view = self.ops.get_review_detail(candidate_id)
        if not view:
            return CliCommandResult(command_path="discovery review show", status="error", errors=["Not found"], exit_code=2)
            
        summary = {
            "candidate_id": view.candidate_id,
            "title": view.canonical_title,
            "brand": view.canonical_brand,
            "status": view.review_status,
            "split_recommended": view.split_recommended,
            "sources": [{"id": s.source_item_id, "title": s.raw_title, "flags": s.ambiguity_flags} for s in view.sources],
            "history": [{"action": h.action, "actor": h.actor, "reason": h.reason} for h in view.audit_history]
        }
        return CliCommandResult(command_path="discovery review show", summary=summary)

    def approve(self, context: CliExecutionContext, candidate_id: str, actor: str) -> CliCommandResult:
        if not context.confirm:
            return CliCommandResult(command_path="discovery review approve", status="error", errors=["--confirm required"], exit_code=1)
        self.ops.approve_candidate(candidate_id, actor, "CLI Approval")
        return CliCommandResult(command_path="discovery review approve", summary={"status": "approved", "candidate_id": candidate_id})

    def reject(self, context: CliExecutionContext, candidate_id: str, actor: str) -> CliCommandResult:
        if not context.confirm:
            return CliCommandResult(command_path="discovery review reject", status="error", errors=["--confirm required"], exit_code=1)
        self.ops.reject_candidate(candidate_id, actor, "CLI Rejection")
        return CliCommandResult(command_path="discovery review reject", summary={"status": "rejected", "candidate_id": candidate_id})

    def hold(self, context: CliExecutionContext, candidate_id: str, actor: str) -> CliCommandResult:
        if not context.confirm:
            return CliCommandResult(command_path="discovery review hold", status="error", errors=["--confirm required"], exit_code=1)
        self.ops.hold_candidate(candidate_id, actor, "CLI Hold")
        return CliCommandResult(command_path="discovery review hold", summary={"status": "hold", "candidate_id": candidate_id})

class DiscoveryAliasCommands:
    def __init__(self, ops_service: DiscoveryReviewOpsService):
        self.ops = ops_service
        
    def list(self, context: CliExecutionContext) -> CliCommandResult:
        aliases = self.ops.list_aliases()
        records = [
            {"id": a.alias_id, "type": a.alias_type, "token": a.token, "resolution": a.resolution, "enabled": a.enabled}
            for a in aliases
        ]
        return CliCommandResult(command_path="discovery alias list", records=records)

    def add(self, context: CliExecutionContext, actor: str, alias_type: str, token: str, resolution: str) -> CliCommandResult:
        alias_id = self.ops.add_alias(actor, alias_type, token, resolution)
        return CliCommandResult(command_path="discovery alias add", summary={"alias_id": alias_id, "status": "added"})

class DiscoverySeedCommands:
    def show(self, context: CliExecutionContext, candidate_id: str) -> CliCommandResult:
        cand = _get_candidate_domain_model(candidate_id)
        if not cand:
            return CliCommandResult(command_path="discovery seed show", status="error", errors=["Candidate not found"], exit_code=2)
        builder = MarketSeedBuilder()
        seed = builder.build_seed(cand)
        
        summary = {
            "keyword_seed": seed.keyword_seed,
            "excluded_keywords": seed.excluded_keywords,
            "gtin_seeds": seed.gtin_seeds
        }
        return CliCommandResult(command_path="discovery seed show", summary=summary)
