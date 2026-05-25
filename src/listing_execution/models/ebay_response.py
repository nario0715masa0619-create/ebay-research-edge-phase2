from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class EBayResponse:
    listing_id: str
    sku: str
    status: str
    item_id: Optional[str] = None
    variation_id: Optional[str] = None
    quantity_sold: int = 0
    timestamp: Optional[datetime] = None
