"""
Unit tests for EBayListingPayloadBuilder.
"""
import pytest
from src.listing_execution.csv_loader import ListingRow
from src.listing_execution.payload_builder import EBayListingPayloadBuilder
from src.listing_execution.image_resolver import SkuImageResolver


class TestEBayListingPayloadBuilder:
    """Test suite for EBayListingPayloadBuilder."""
    
    def setup_method(self):
        """Setup for each test."""
        self.builder = EBayListingPayloadBuilder()
    
    def test_build_valid_payload(self):
        """Test building a valid payload from a CSV row."""
        row = ListingRow(
            sku="SKU0001",
            title="Test Item",
            description="Test Description",
            price=99.99,
            quantity=1,
            condition="Used",
            brand="TestBrand",
            mpn="TEST123",
            row_number=2
        )
        
        payload = self.builder.build(
            listing_row=row,
            seller="test_seller",
            environment="sandbox",
            dry_run=True
        )
        
        assert payload is not None
        assert payload.sku == "SKU0001"
        assert payload.title == "Test Item"
        assert payload.price == 99.99
        assert payload.dry_run is True
        assert len(payload.image_urls) == 3  # SKU0001 has 3 images
    
    def test_build_fails_for_missing_images(self):
        """Test that build fails when images don't exist."""
        row = ListingRow(
            sku="SKU9999",
            title="Test Item",
            description="Test Description",
            price=99.99,
            quantity=1,
            condition="Used",
            brand="TestBrand",
            mpn="TEST123",
            row_number=2
        )
        
        payload = self.builder.build(
            listing_row=row,
            seller="test_seller",
            environment="sandbox",
            dry_run=True
        )
        
        assert payload is None
    
    def test_dry_run_flag(self):
        """Test that dry_run flag is correctly set."""
        row = ListingRow(
            sku="SKU0002",
            title="Test Item",
            description="Test Description",
            price=49.99,
            quantity=1,
            condition="New",
            brand=None,
            mpn=None,
            row_number=2
        )
        
        payload_dry = self.builder.build(row, seller="test", dry_run=True)
        payload_live = self.builder.build(row, seller="test", dry_run=False)
        
        assert payload_dry.dry_run is True
        assert payload_live.dry_run is False
