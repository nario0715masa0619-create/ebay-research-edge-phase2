import logging
from typing import Optional, Dict, Any
from sqlalchemy import select, or_

from src.db.session import SessionManager
from src.db.models import NormalizedSourceItemModel, CanonicalProductCandidateModel, MatchEvidenceModel
from src.discovery.candidate_normalizer import CandidateNormalizer
from src.discovery.models import NormalizedSourceItem

logger = logging.getLogger(__name__)

class SourceNormalizationRunnerAdapter:
    """
    Adapter that connects the Orchestrator to the CandidateNormalizer for batch refinement.
    """
    
    def __init__(self, normalizer: CandidateNormalizer, session_manager: Optional[SessionManager] = None):
        self.normalizer = normalizer
        self.session_manager = session_manager or SessionManager()
        
    def run_refinement_job(self, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """
        Job executed by the ScheduledOrchestrator to refine existing normalized items.
        """
        logger.info(f"Starting Source Normalization Refinement Job (limit={limit})")
        
        processed = 0
        refined = 0
        review_flagged = 0
        
        with self.session_manager.session() as session:
            # Phase B Selection Criteria:
            # - review_required = true OR
            # - variation_keys_json IS NULL OR
            # - bundle_flags_json IS NULL
            stmt = select(NormalizedSourceItemModel).where(
                or_(
                    NormalizedSourceItemModel.review_required == True,
                    NormalizedSourceItemModel.variation_keys_json == None,
                    NormalizedSourceItemModel.bundle_flags_json == None
                )
            ).order_by(NormalizedSourceItemModel.updated_at.desc()).limit(limit)
            
            items = session.execute(stmt).scalars().all()
            
            for db_item in items:
                processed += 1
                
                # Convert to domain
                domain_item = NormalizedSourceItem(
                    normalized_item_id=db_item.normalized_item_id,
                    source_item_id=db_item.source_item_id,
                    normalized_title=db_item.normalized_title,
                    normalized_brand=db_item.normalized_brand,
                    normalized_model=db_item.normalized_model,
                    normalized_mpn=db_item.normalized_mpn,
                    strict_gtins=db_item.strict_gtins_json or [],
                    loose_gtins=db_item.loose_gtins_json or [],
                    normalized_condition=db_item.normalized_condition,
                    normalized_quantity=db_item.normalized_quantity,
                    variation_keys=db_item.variation_keys_json or {},
                    bundle_flags=db_item.bundle_flags_json or [],
                    parsed_attributes=db_item.parsed_attributes_json or {},
                    review_required=db_item.review_required
                )
                
                # Refine!
                result = self.normalizer.refine(domain_item)
                
                # Update DB Item
                db_item.variation_keys_json = result.normalized_item.variation_keys
                db_item.bundle_flags_json = result.normalized_item.bundle_flags
                db_item.review_required = result.review_required
                
                # If a candidate was found/updated, we should ideally persist it
                # For Phase B simplicity, we update candidate confidence/review flag if it exists
                if result.candidate:
                    cand_model = session.execute(
                        select(CanonicalProductCandidateModel)
                        .where(CanonicalProductCandidateModel.candidate_id == result.candidate.candidate_id)
                    ).scalar_one_or_none()
                    
                    if cand_model:
                        cand_model.review_required = result.candidate.review_required
                        
                # Update Evidence if available
                if result.evidence:
                    ev_model = session.execute(
                        select(MatchEvidenceModel)
                        .where(MatchEvidenceModel.evidence_id == result.evidence.evidence_id)
                    ).scalar_one_or_none()
                    
                    if ev_model:
                        ev_model.variation_penalty = result.evidence.variation_penalty
                        ev_model.bundle_penalty = result.evidence.bundle_penalty
                        ev_model.ambiguity_flags_json = result.evidence.ambiguity_flags
                        ev_model.explanation_lines_json = result.evidence.explanation_lines
                        
                refined += 1
                if result.review_required:
                    review_flagged += 1
                    
            session.commit()
            
        logger.info(f"Refinement Job Complete: processed={processed}, refined={refined}, flagged_for_review={review_flagged}")
        
        return {
            "status": "completed",
            "processed_count": processed,
            "refined_count": refined,
            "review_count": review_flagged
        }
