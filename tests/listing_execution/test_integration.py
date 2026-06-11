"""
Integration tests for the eBay listing flow.
"""
import pytest
from pathlib import Path
from src.listing_execution.csv_loader import EBayListingCSVLoader
from src.listing_execution.payload_builder import EBayListingPayloadBuilder
from src.listing_execution.audit_logger import ExecutionAuditLogger
import json


class TestEBayListingIntegration:
    """Integration tests for the complete eBay listing flow."""
    
    def setup_method(self):
        """Setup for each test."""
        self.csv_loader = EBayListingCSVLoader("data/listings_sample.csv")
        self.payload_builder = EBayListingPayloadBuilder()
        self.audit_logger = ExecutionAuditLogger("logs/test_integration_audit.jsonl")
    
    def test_end_to_end_dry_run_flow(self):
        """Test the complete dry-run flow from CSV to audit log."""
        # Load CSV
        csv_result = self.csv_loader.load()
        assert len(csv_result.rows) == 3
        assert len(csv_result.errors) == 0
        
        # Build payloads
        payloads = []
        for row in csv_result.rows:
            payload = self.payload_builder.build(
                listing_row=row,
                seller="integration_test",
                environment="sandbox",
                dry_run=True
            )
            assert payload is not None
            payloads.append(payload)
        
        assert len(payloads) == 3
        
        # Log execution
        for payload in payloads:
            self.audit_logger.log_execution_start(payload)
            self.audit_logger.log_execution_success(
                sku=payload.sku,
                listing_id=payload.listing_id,
                attempt_id=payload.attempt_id,
                mode="dry_run",
                image_count=len(payload.image_urls)
            )
        
        # Verify audit log
        log_file = Path("logs/test_integration_audit.jsonl")
        assert log_file.exists()
        
        lines = log_file.read_text(encoding='utf-8').strip().split('\n')
        records = [json.loads(line) for line in lines if line.strip()]
        assert len(records) > 0
    
    def test_skipped_sku_with_missing_images(self):
        """Test that SKUs with missing images are skipped."""
        from src.listing_execution.csv_loader import ListingRow
        
        # Create a row with a non-existent SKU
        row = ListingRow(
            sku="MISSING_SKU",
            title="Missing Images Item",
            description="This SKU has no images",
            price=199.99,
            quantity=1,
            condition="New",
            brand=None,
            mpn=None,
            row_number=99
        )
        
        payload = self.payload_builder.build(row, seller="test", dry_run=True)
        assert payload is None
        
        self.audit_logger.log_execution_skip(row.sku, "No valid images found")
        
        # Verify skip was logged
        log_file = Path("logs/test_integration_audit.jsonl")
        lines = log_file.read_text(encoding='utf-8').strip().split('\n')
        records = [json.loads(line) for line in lines if line.strip()]
        skip_records = [r for r in records if r.get('event') == 'execution_skip']
        assert any(r['sku'] == 'MISSING_SKU' for r in skip_records)
