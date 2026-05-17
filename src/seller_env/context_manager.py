import threading
from typing import Optional
from src.seller_env.models import SellerContext

class SellerContextManager:
    """
    Manages the current seller context in a thread-local or session-scoped manner.
    """
    _storage = threading.local()

    @classmethod
    def set_context(cls, context: SellerContext):
        cls._storage.current_context = context

    @classmethod
    def get_context(cls) -> Optional[SellerContext]:
        return getattr(cls._storage, "current_context", None)

    @classmethod
    def clear_context(cls):
        if hasattr(cls._storage, "current_context"):
            del cls._storage.current_context

    @property
    def current(self) -> Optional[SellerContext]:
        return self.get_context()
