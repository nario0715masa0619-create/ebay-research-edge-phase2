from typing import Optional
from sqlalchemy.orm import Session
from src.db.models import NormalizedSourceItemModel
from src.discovery.models import NormalizedSourceItem

class PersistentNormalizedSourceItemRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, item: NormalizedSourceItem) -> None:
        with self.session_factory() as session:
            model = NormalizedSourceItemModel(
                normalized_item_id=item.normalized_item_id,
                source_item_id=item.source_item_id,
                normalized_title=item.normalized_title,
                normalized_brand=item.normalized_brand,
                normalized_model=item.normalized_model,
                normalized_mpn=item.normalized_mpn,
                strict_gtins_json=item.strict_gtins,
                loose_gtins_json=item.loose_gtins,
                normalized_condition=item.normalized_condition,
                normalized_quantity=item.normalized_quantity,
                variation_keys_json=item.variation_keys,
                bundle_flags_json=item.bundle_flags,
                parsed_attributes_json=item.parsed_attributes,
                identity_signals_json=item.identity_signals,
                normalization_flags_json=item.normalization_flags,
                review_required=item.review_required,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            session.add(model)
            session.commit()
