"""
Unit tests for EBayListingCSVLoader.
"""
import pytest
from pathlib import Path
from src.listing_execution.csv_loader import EBayListingCSVLoader


class TestEBayListingCSVLoader:
    """Test suite for EBayListingCSVLoader."""
    
    def setup_method(self):
        """Setup for each test."""
        self.loader = EBayListingCSVLoader("data/listings_sample.csv")
    
    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        result = self.loader.load()
        assert len(result.rows) == 3
        assert all(row.sku for row in result.rows)
        assert all(row.title for row in result.rows)
        assert all(row.price > 0 for row in result.rows)
    
    def test_csv_row_structure(self):
        """Test that CSV rows are correctly parsed."""
        result = self.loader.load()
        first_row = result.rows[0]
        assert first_row.sku == "SKU0001"
        assert "Canon" in first_row.title
        assert first_row.price == 129.99
        assert first_row.condition == "Used"
    
    def test_nonexistent_file(self):
        """Test loading a nonexistent file."""
        loader = EBayListingCSVLoader("nonexistent.csv")
        result = loader.load()
        assert len(result.rows) == 0
        assert len(result.errors) > 0
    
    def test_optional_columns(self):
        """Test that optional columns (brand, mpn) are parsed."""
        result = self.loader.load()
        first_row = result.rows[0]
        assert first_row.brand == "Canon"
        assert first_row.mpn == "EF50"
