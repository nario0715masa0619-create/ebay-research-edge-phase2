from typing import Optional
from pydantic import BaseModel, Field

class WebQueryParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    q: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    channel: Optional[str] = None
    source_layer: Optional[str] = None
    event_type: Optional[str] = None
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None
    marketplace_id: Optional[str] = None
    dry_run: bool = False
