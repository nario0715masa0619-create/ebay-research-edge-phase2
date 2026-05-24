import json
from sqlalchemy.orm import Session
from src.db.models import CanonicalProductCandidateModel
from src.market_eval.bootstrap import MarketEvalBootstrap
from src.market_eval.market_evaluation_service import MarketEvaluationService
from src.repositories.persistent_market_evaluation_repository import PersistentMarketEvaluationRepository

class MarketEvalOpsService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = MarketEvalBootstrap.get_settings()
        self.gateway = MarketEvalBootstrap.get_gateway()
        self.service = MarketEvaluationService(self.settings, self.gateway)
        self.repo = PersistentMarketEvaluationRepository(self.db)
        
    def evaluate_candidate(self, candidate_id: str):
        candidate = self.db.query(CanonicalProductCandidateModel).filter_by(candidate_id=candidate_id).first()
        if not candidate:
            print(f"Error: Candidate '{candidate_id}' not found.")
            return None
            
        print(f"Evaluating candidate: {candidate_id} ({candidate.canonical_title})")
        print(f"Provider: {self.settings.market_data_provider}")
        
        result, evidence = self.service.evaluate_candidate(candidate)
        
        print("\n--- Result ---")
        print(f"Status: {result.evaluation_status}")
        print(f"Confidence: {result.market_confidence:.2f}")
        print(f"Price Band: ${result.price_low} - ${result.price_median} - ${result.price_high}")
        print(f"Comparables: {result.comparable_count} (out of {result.raw_result_count})")
        print(f"Unsafe Reasons: {result.unsafe_reasons}")
        
        print("\nSaving to DB...")
        self.repo.save_result(result)
        self.repo.save_evidence(evidence)
        print("Done.")
        
        return result
