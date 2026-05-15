import pytest
from datetime import datetime
from src.ebay.models import SourceItem, ProductCandidate
from src.repositories.source_item_repository import SourceItemRepository
from src.repositories.product_candidate_repository import ProductCandidateRepository
from src.repositories.candidate_evidence_repository import CandidateEvidenceRepository
from src.repositories.job_run_repository import JobRunRepository
from src.research_pipeline.pipeline import CandidatePipeline
from src.research_pipeline.models import CandidateBuildRequest

@pytest.fixture
def pipeline_setup():
    source_repo = SourceItemRepository()
    candidate_repo = ProductCandidateRepository()
    evidence_repo = CandidateEvidenceRepository()
    job_repo = JobRunRepository()
    pipeline = CandidatePipeline(source_repo, candidate_repo, evidence_repo, job_repo)
    return pipeline, source_repo, candidate_repo, evidence_repo, job_repo

def test_pbandai_manual_preban(pipeline_setup):
    # 1. pbandai が manual_preban に分岐する
    pipeline, source_repo, candidate_repo, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="pb1", source_platform="pbandai", source_url="url",
        source_title="PB Item", source_price_jpy=1000,
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="pb1"))
    assert res.pipeline_type == "manual_preban"
    assert res.decision_type == "excluded"
    assert res.exclude_reason == "preban"

def test_not_buy_now_excluded(pipeline_setup):
    # 2. buy_now 以外が excluded になる
    pipeline, source_repo, _, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="auc1", source_platform="mercari", source_url="url",
        source_title="Auction Item", source_price_jpy=1000, source_purchase_type="auction",
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="auc1"))
    assert res.decision_type == "excluded"
    assert res.exclude_reason == "not_buy_now"

def test_out_of_stock_excluded(pipeline_setup):
    # 3. 在庫なしが excluded になる
    pipeline, source_repo, _, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="sold1", source_platform="mercari", source_url="url",
        source_title="Sold Item", source_price_jpy=1000, source_stock_status="sold_out",
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="sold1"))
    assert res.decision_type == "excluded"
    assert res.exclude_reason == "out_of_stock"

def test_successful_candidate_generation(pipeline_setup):
    # 4. 正常系で ProductCandidate が生成される
    pipeline, source_repo, candidate_repo, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="item1", source_platform="mercari", source_url="url",
        source_title="Good Item", source_price_jpy=50000, # Enough profit
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="item1"))
    
    assert res.success_flag is True
    assert res.decision_type == "candidate"
    assert res.status == "candidate"
    
    candidate = candidate_repo.get_by_candidate_id(res.candidate_id)
    assert candidate.source_item_id == "item1"
    assert candidate.sku.startswith("AUTO-ME")

def test_resolver_outputs_reflected(pipeline_setup):
    # 5. 各 Resolver 出力が candidate に反映される
    pipeline, source_repo, candidate_repo, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="item2", source_platform="mercari", source_url="url", 
        source_title="T", source_price_jpy=50000,
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="item2"))
    candidate = candidate_repo.get_by_candidate_id(res.candidate_id)
    assert candidate.expected_profit_jpy > 0
    assert candidate.standard_score > 0
    assert candidate.score_grade in ["A", "B", "C", "D", "E"]

def test_evidence_storage(pipeline_setup):
    # 6. CandidateEvidence が複数保存される
    pipeline, source_repo, _, evidence_repo, _ = pipeline_setup
    item = SourceItem(
        source_item_id="item3", source_platform="mercari", source_url="url", 
        source_title="T", source_price_jpy=50000,
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="item3"))
    evidences = evidence_repo.list_by_candidate_id(res.candidate_id)
    assert len(evidences) >= 6 # shipping, import, selling, payout, total, score
    e_types = [e.evidence_type for e in evidences]
    assert "shipping" in e_types
    assert "score" in e_types

def test_low_margin_excluded(pipeline_setup):
    # 7. 利益不足で excluded(low_margin) になる
    pipeline, source_repo, _, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="item4", source_platform="mercari", source_url="url", 
        source_title="T", source_price_jpy=1000, # 1000 is low for 2.0x sale with 20 shipping
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="item4"))
    assert res.decision_type == "excluded"
    assert res.exclude_reason == "low_margin"

def test_idempotency_no_duplicate(pipeline_setup):
    # 9. 同一 source item 再実行で upsert され、重複作成されない
    pipeline, source_repo, candidate_repo, _, _ = pipeline_setup
    item = SourceItem(
        source_item_id="dup1", source_platform="mercari", source_url="url", 
        source_title="T", source_price_jpy=50000,
        source_image_urls=["http://example.com/1.jpg"]
    )
    source_repo.save(item)
    
    res1 = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="dup1"))
    res2 = pipeline.build_research_candidate(CandidateBuildRequest(source_item_id="dup1"))
    
    assert res1.candidate_id == res2.candidate_id
    assert len(candidate_repo._candidates) == 1

def test_job_run_tracking(pipeline_setup):
    # 10. JobRun に件数が記録される
    pipeline, source_repo, _, _, job_repo = pipeline_setup
    source_repo.save(SourceItem(
        source_item_id="j1", source_platform="mercari", source_url="u", 
        source_title="T", source_price_jpy=50000,
        source_image_urls=["http://example.com/1.jpg"]
    ))
    source_repo.save(SourceItem(
        source_item_id="j2", source_platform="pbandai", source_url="u", 
        source_title="T", source_price_jpy=50000,
        source_image_urls=["http://example.com/1.jpg"]
    ))
    
    batch_res = pipeline.run_research_candidate_pipeline(limit=10)
    assert batch_res.processed_count == 2
    assert batch_res.candidate_count == 1
    assert batch_res.excluded_count == 1
    
    job = job_repo.get_run(batch_res.run_id)
    assert job.status == "completed"
    assert job.finished_at is not None
