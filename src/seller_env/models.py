from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class SellerProfile:
    seller_account_id: str
    seller_name: str
    seller_label: str
    enabled: bool = True
    environment_mode: str = "mixed" # sandbox, production, mixed
    default_marketplace_id: str = "EBAY_US"
    default_currency: str = "USD"
    default_merchant_location_key: Optional[str] = None
    default_fulfillment_policy_id: Optional[str] = None
    default_payment_policy_id: Optional[str] = None
    default_return_policy_id: Optional[str] = None
    auth_profile_ref: Optional[str] = None
    notification_profile_ref: Optional[str] = None
    scheduling_profile_ref: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EnvironmentProfile:
    environment_id: str
    environment_name: str
    environment_type: str # sandbox, production
    enabled: bool = True
    ebay_api_base_url: str = ""
    ebay_oauth_base_url: str = ""
    application_keyset_ref: Optional[str] = None
    supports_live_publish: bool = False
    supports_test_users: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SellerEnvironmentBinding:
    binding_id: str
    seller_account_id: str
    environment_id: str
    active_flag: bool = False
    marketplace_id: str = "EBAY_US"
    currency: str = "USD"
    merchant_location_key: Optional[str] = None
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    refresh_token_ref: Optional[str] = None
    auth_scope_profile: Optional[str] = None
    notification_channel_profile: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SellerContext:
    seller_account_id: str
    seller_label: str
    environment_type: str
    marketplace_id: str
    currency: str
    merchant_location_key: Optional[str] = None
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    auth_profile_ref: Optional[str] = None
    notification_profile_ref: Optional[str] = None
    dry_run_default: bool = False
    publish_enabled: bool = False
    monitoring_enabled: bool = True
    sync_enabled: bool = True

@dataclass
class SellerPolicySnapshot:
    snapshot_id: str
    seller_account_id: str
    environment_id: str
    marketplace_id: str
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.now)

    @property
    def policy_type(self) -> str:
        if self.fulfillment_policy_id:
            return "Fulfillment"
        elif self.payment_policy_id:
            return "Payment"
        elif self.return_policy_id:
            return "Return"
        return "Unknown"

@dataclass
class SellerLocationSnapshot:
    snapshot_id: str
    seller_account_id: str
    environment_id: str
    merchant_location_key: str
    payload: Dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.now)
