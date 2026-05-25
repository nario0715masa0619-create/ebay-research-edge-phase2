from enum import Enum

class ListingState(Enum):
    pending = "pending"
    active = "active"
    scheduled = "scheduled"
    failed = "failed"
    pending_retry = "pending_retry"
    rolled_back = "rolled_back"
