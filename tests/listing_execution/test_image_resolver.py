"""
Unit tests for SkuImageResolver.
"""
import pytest
from pathlib import Path
from src.listing_execution.image_resolver import SkuImageResolver, ImageValidationResult


class TestSkuImageResolver:
    """Test suite for SkuImageResolver."""
    
    def setup_method(self):
        """Setup for each test."""
        self.resolver = SkuImageResolver(base_dir=Path("data/images"))
    
    def test_resolve_valid_sku_with_multiple_images(self):
        """Test resolving a valid SKU with multiple images."""
        result = self.resolver.resolve("SKU0001")
        assert result.is_valid
        assert result.image_count == 3
        assert len(result.image_paths) == 3
        assert all(p.suffix.lower() in ['.jpg', '.jpeg', '.png'] for p in result.image_paths)
    
    def test_resolve_valid_sku_with_single_image(self):
        """Test resolving a valid SKU with a single image."""
        result = self.resolver.resolve("SKU0003")
        assert result.is_valid
        assert result.image_count == 1
    
    def test_resolve_nonexistent_sku(self):
        """Test resolving a SKU that doesn't exist."""
        result = self.resolver.resolve("SKU9999")
        assert not result.is_valid
        assert result.image_count == 0
        assert len(result.errors) > 0
    
    def test_resolve_empty_sku(self):
        """Test resolving with an empty SKU."""
        result = self.resolver.resolve("")
        assert not result.is_valid
        assert "empty" in " ".join(result.errors).lower()
    
    def test_image_files_are_sorted(self):
        """Test that images are returned in sorted order."""
        result = self.resolver.resolve("SKU0001")
        assert result.is_valid
        names = [p.name for p in result.image_paths]
        assert names == sorted(names)
