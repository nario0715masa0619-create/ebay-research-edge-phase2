from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.ebay.models import SourceItem
from src.db.models import SourceItemModel

class PersistentSourceItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, source_item: SourceItem):
        model = SourceItemModel(
            source_item_id=source_item.source_item_id,
            source_platform=source_item.source_platform,
            source_url=source_item.source_url,
            source_title=source_item.source_title,
            source_price_jpy=source_item.source_price_jpy,
            source_shipping_jpy=source_item.source_shipping_jpy,
            source_stock_status=source_item.source_stock_status,
            source_purchase_type=source_item.source_purchase_type,
            image_urls_json=source_item.source_image_urls,
            raw_json=source_item.source_raw_json,
            collected_at=source_item.collected_at
        )
        self.session.add(model)

    def get_by_id(self, source_item_id: str) -> Optional[SourceItem]:
        stmt = select(SourceItemModel).where(SourceItemModel.source_item_id == source_item_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def get_by_platform_and_url(self, platform: str, url: str) -> Optional[SourceItem]:
        stmt = select(SourceItemModel).where(SourceItemModel.source_platform == platform, SourceItemModel.source_url == url)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def list_unprocessed(self, limit: Optional[int] = None) -> List[SourceItem]:
        stmt = select(SourceItemModel)
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def mark_processed(self, source_item_id: str):
        # Placeholder
        pass

    def upsert(self, source_item: SourceItem):
        existing = self.get_by_platform_and_url(source_item.source_platform, source_item.source_url)
        if existing:
            stmt = update(SourceItemModel).where(SourceItemModel.source_platform == source_item.source_platform, SourceItemModel.source_url == source_item.source_url).values(
                source_title=source_item.source_title,
                source_price_jpy=source_item.source_price_jpy,
                source_shipping_jpy=source_item.source_shipping_jpy,
                source_stock_status=source_item.source_stock_status,
                source_purchase_type=source_item.source_purchase_type,
                image_urls_json=source_item.source_image_urls,
                raw_json=source_item.source_raw_json,
                updated_at=source_item.collected_at
            )
            self.session.execute(stmt)
        else:
            self.save(source_item)

    def _to_domain(self, model: SourceItemModel) -> SourceItem:
        return SourceItem(
            source_item_id=model.source_item_id,
            source_platform=model.source_platform,
            source_url=model.source_url,
            source_title=model.source_title,
            source_price_jpy=model.source_price_jpy,
            source_shipping_jpy=model.source_shipping_jpy,
            source_stock_status=model.source_stock_status,
            source_purchase_type=model.source_purchase_type,
            source_image_urls=model.image_urls_json or [],
            source_raw_json=model.raw_json or {},
            collected_at=model.collected_at
        )
