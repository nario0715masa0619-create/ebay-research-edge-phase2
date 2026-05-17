import math
from typing import List, Dict, Any
from urllib.parse import urlencode

class PaginationHelper:
    def __init__(self, total_items: int, page: int, page_size: int, base_url: str, current_params: Dict[str, Any]):
        self.total_items = total_items
        self.page = max(1, page)
        self.page_size = max(1, page_size)
        self.base_url = base_url
        self.current_params = current_params.copy()
        
        # Calculate totals
        self.total_pages = max(1, math.ceil(total_items / page_size))
        if self.page > self.total_pages:
            self.page = self.total_pages
            
        self.start_index = (self.page - 1) * self.page_size + 1 if total_items > 0 else 0
        self.end_index = min(self.page * self.page_size, total_items)
        
    @property
    def has_previous(self) -> bool:
        return self.page > 1
        
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
        
    def page_url(self, target_page: int) -> str:
        params = self.current_params.copy()
        params["page"] = target_page
        # Filter out None/empty values to keep url clean
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        query_string = urlencode(clean_params)
        return f"{self.base_url}?{query_string}"
        
    def get_visible_pages(self, max_visible: int = 5) -> List[int]:
        half = max_visible // 2
        start = max(1, self.page - half)
        end = min(self.total_pages, start + max_visible - 1)
        
        if end - start < max_visible - 1:
            start = max(1, end - max_visible + 1)
            
        return list(range(start, end + 1))
