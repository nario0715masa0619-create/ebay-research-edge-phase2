from typing import Any, Dict, Optional
from src.admin_cli.bootstrap import AdminCliBootstrap, AdminCliAppContainer
from src.db.session import SessionManager

class WebBootstrap:
    _container: Optional[AdminCliAppContainer] = None

    @classmethod
    def get_container(cls) -> AdminCliAppContainer:
        if cls._container is None:
            # Leverage existing CLI bootstrap to construct all components cleanly
            cls._container = AdminCliBootstrap.bootstrap()
        return cls._container

    @classmethod
    def get_db_session(cls):
        # Retrieve active session from session manager
        session_manager = SessionManager()
        return session_manager.get_session()
