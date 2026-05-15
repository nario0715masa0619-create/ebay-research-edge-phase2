from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class EbayApiItemSummary:
    item_id: str
    title: str
    price: Dict[str, str]  # {"value": "100.00", "currency": "USD"}
    shipping_options: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EbayApiItemDetail:
    item_id: str
    title: str
    price: Dict[str, str]
    shipping_options: List[Dict[str, Any]] = field(default_factory=list)
    taxes: List[Dict[str, Any]] = field(default_factory=list)
    return_terms: Dict[str, Any] = field(default_factory=dict)
    estimated_import_costs: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
