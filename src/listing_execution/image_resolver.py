"""
SKU-based image resolver for eBay listings.
Reads images from data/images/{sku}/ directory.
"""
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ImageValidationResult:
    """Result of image validation for a SKU."""
    sku: str
    is_valid: bool
    image_paths: List[Path]  # Sorted by filename
    image_count: int
    errors: List[str]
    warnings: List[str]
    validated_at: datetime

class SkuImageResolver:
    """
    Resolves and validates images for a given SKU.
    Images are expected in: data/images/{sku}/
    
    Rules:
    1. Directory must exist
    2. At least 1 image required
    3. Only .jpg, .jpeg, .png allowed
    4. Files sorted by filename (ascending)
    5. No zero-sized files
    6. No corrupted images
    """
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    DEFAULT_IMAGE_BASE_DIR = Path("data/images")
    MAX_IMAGES = 12  # eBay limit
    MIN_IMAGE_SIZE = 1  # bytes
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize resolver with optional custom base directory."""
        self.base_dir = base_dir or self.DEFAULT_IMAGE_BASE_DIR
        
    def resolve(self, sku: str) -> ImageValidationResult:
        """
        Resolve and validate images for the given SKU.
        Returns ImageValidationResult with all metadata.
        """
        errors = []
        warnings = []
        image_paths = []
        
        # Step 1: Validate SKU
        if not sku or not sku.strip():
            errors.append("SKU is empty or whitespace")
            return ImageValidationResult(
                sku=sku,
                is_valid=False,
                image_paths=[],
                image_count=0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now()
            )
        
        sku = sku.strip()
        
        # Step 2: Locate SKU directory
        sku_dir = self.base_dir / sku
        
        if not sku_dir.exists():
            errors.append(f"Image directory does not exist: {sku_dir}")
            return ImageValidationResult(
                sku=sku,
                is_valid=False,
                image_paths=[],
                image_count=0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now()
            )
        
        if not sku_dir.is_dir():
            errors.append(f"Path exists but is not a directory: {sku_dir}")
            return ImageValidationResult(
                sku=sku,
                is_valid=False,
                image_paths=[],
                image_count=0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now()
            )
        
        # Step 3: Collect allowed image files
        try:
            candidate_files = [
                f for f in sku_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.ALLOWED_EXTENSIONS
            ]
        except OSError as e:
            errors.append(f"Cannot read directory {sku_dir}: {str(e)}")
            return ImageValidationResult(
                sku=sku,
                is_valid=False,
                image_paths=[],
                image_count=0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now()
            )
        
        # Step 4: Sort by filename (ascending)
        candidate_files.sort(key=lambda f: f.name)
        
        # Step 5: Validate each file
        for file_path in candidate_files:
            try:
                # Check file size
                file_size = file_path.stat().st_size
                if file_size < self.MIN_IMAGE_SIZE:
                    errors.append(f"Image file is zero-sized or too small: {file_path.name} ({file_size} bytes)")
                    continue
                
                # Basic corruption check (attempt to read)
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if not header:
                        errors.append(f"Cannot read image file: {file_path.name}")
                        continue
                
                # For now, basic validation passed
                image_paths.append(file_path)
                
            except Exception as e:
                errors.append(f"Error validating {file_path.name}: {str(e)}")
                continue
        
        # Step 6: Check minimum image count
        if len(image_paths) == 0:
            errors.append(f"No valid images found in {sku_dir}")
            return ImageValidationResult(
                sku=sku,
                is_valid=False,
                image_paths=[],
                image_count=0,
                errors=errors,
                warnings=warnings,
                validated_at=datetime.now()
            )
        
        # Step 7: Check for exceeding max images
        if len(image_paths) > self.MAX_IMAGES:
            warnings.append(f"Found {len(image_paths)} images, but eBay limit is {self.MAX_IMAGES}. Will use first {self.MAX_IMAGES}.")
            image_paths = image_paths[:self.MAX_IMAGES]
        
        # Step 8: Success
        return ImageValidationResult(
            sku=sku,
            is_valid=True,
            image_paths=image_paths,
            image_count=len(image_paths),
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now()
        )
    
    def get_image_urls_for_upload(self, sku: str) -> Tuple[List[Path], List[str]]:
        """
        Convenience method: returns (image_paths, errors).
        If errors, image_paths is empty.
        """
        result = self.resolve(sku)
        if result.is_valid:
            return result.image_paths, []
        else:
            return [], result.errors
