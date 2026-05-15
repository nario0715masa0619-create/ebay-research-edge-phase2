from typing import Optional, List
from datetime import datetime
from src.ebay.models import SourceItem

class SourceItemRepository:
    def __init__(self):
        self._items = {}  # {source_item_id: SourceItem}

    def get_by_id(self, source_item_id: str) -> Optional[SourceItem]:
        return self._items.get(source_item_id)

    def list_unprocessed(self, limit: Optional[int] = None) -> List[SourceItem]:
        unprocessed = [item for item in self._items.values() if item.processed_at is None]
        if limit:
            return unprocessed[:limit]
        return unprocessed

    def save(self, source_item: SourceItem):
        self._items[source_item.source_item_id] = source_item

    def mark_processed(self, source_item_id: str, processed_at: datetime = None):
        if not processed_at:
            processed_at = datetime.now()
        item = self.get_by_id(source_item_id)
        if item:
            item.processed_at = processed_at
