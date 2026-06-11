"""
CSV loader for eBay listing data.
Reads product information from CSV file.
Expected columns: sku,title,description,price,quantity,condition,brand,mpn
"""
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import csv
import logging

logger = logging.getLogger(__name__)

@dataclass
class ListingRow:
    """Single row from the CSV."""
    sku: str
    title: str
    description: str
    price: float
    quantity: int
    condition: str
    brand: Optional[str]
    mpn: Optional[str]
    row_number: int  # 1-indexed for error reporting

@dataclass
class LoadResult:
    """Result of CSV loading."""
    rows: List[ListingRow]
    errors: List[str]
    warnings: List[str]
    loaded_at: datetime

class EBayListingCSVLoader:
    """
    Loads eBay listing data from a CSV file.
    
    Expected format:
    sku,title,description,price,quantity,condition,brand,mpn
    SKU0001,Canon Lens 50mm,Used good condition,129.99,1,Used,Canon,EF50
    SKU0002,Nike Shoes US9,Light wear,79.99,1,Used,Nike,NA
    """
    
    REQUIRED_COLUMNS = ['sku', 'title', 'description', 'price', 'quantity', 'condition']
    OPTIONAL_COLUMNS = ['brand', 'mpn']
    
    def __init__(self, file_path: str = "data/listings.csv"):
        """Initialize with CSV file path."""
        self.file_path = Path(file_path)
    
    def load(self) -> LoadResult:
        """
        Load and validate CSV file.
        Returns LoadResult with rows and error details.
        """
        errors = []
        warnings = []
        rows = []
        skus_seen = set()
        
        # Check file exists
        if not self.file_path.exists():
            errors.append(f"CSV file not found: {self.file_path}")
            return LoadResult(rows=[], errors=errors, warnings=warnings, loaded_at=datetime.now())
        
        try:
            with open(self.file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    errors.append("CSV file is empty or has no header")
                    return LoadResult(rows=[], errors=errors, warnings=warnings, loaded_at=datetime.now())
                
                # Validate column headers
                for required_col in self.REQUIRED_COLUMNS:
                    if required_col not in reader.fieldnames:
                        errors.append(f"Missing required column: {required_col}")
                
                if errors:
                    return LoadResult(rows=[], errors=errors, warnings=warnings, loaded_at=datetime.now())
                
                # Parse rows
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1=header)
                    try:
                        # Extract required fields
                        sku = row.get('sku', '').strip()
                        title = row.get('title', '').strip()
                        description = row.get('description', '').strip()
                        condition = row.get('condition', '').strip()
                        
                        # Parse numeric fields
                        try:
                            price = float(row.get('price', '0'))
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid price value: {row.get('price')}")
                            continue
                        
                        try:
                            quantity = int(row.get('quantity', '1'))
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid quantity value: {row.get('quantity')}")
                            continue
                        
                        # Validate required fields
                        if not sku:
                            errors.append(f"Row {row_num}: SKU is empty")
                            continue
                        
                        if not title:
                            errors.append(f"Row {row_num}: Title is empty")
                            continue
                        
                        if price <= 0:
                            errors.append(f"Row {row_num}: Price must be > 0, got {price}")
                            continue
                        
                        if quantity < 1:
                            errors.append(f"Row {row_num}: Quantity must be >= 1, got {quantity}")
                            continue
                        
                        if not condition:
                            errors.append(f"Row {row_num}: Condition is empty")
                            continue
                        
                        # Check for duplicate SKU
                        if sku in skus_seen:
                            warnings.append(f"Row {row_num}: Duplicate SKU '{sku}' (will skip)")
                            continue
                        
                        skus_seen.add(sku)
                        
                        # Extract optional fields
                        brand = row.get('brand', '').strip() or None
                        mpn = row.get('mpn', '').strip() or None
                        
                        listing_row = ListingRow(
                            sku=sku,
                            title=title,
                            description=description,
                            price=price,
                            quantity=quantity,
                            condition=condition,
                            brand=brand,
                            mpn=mpn,
                            row_number=row_num
                        )
                        rows.append(listing_row)
                    
                    except Exception as e:
                        errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
                        continue
        
        except Exception as e:
            errors.append(f"Cannot read CSV file: {str(e)}")
        
        return LoadResult(rows=rows, errors=errors, warnings=warnings, loaded_at=datetime.now())
