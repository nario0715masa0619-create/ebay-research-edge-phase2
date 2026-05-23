from typing import Optional
from datetime import datetime
import logging

from src.db.session import SessionManager
from src.escalation.bootstrap import EscalationBootstrap

logger = logging.getLogger(__name__)

class EscalationReminderRunnerAdapter:
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()

    def run_escalation_reminder_runner(
        self,
        dry_run: bool = False,
        limit: Optional[int] = None,
        seller_account_id: Optional[str] = None,
        environment_type: Optional[str] = None,
        **kwargs
    ):
        logger.info(
            f"EscalationReminderRunnerAdapter triggered. dry_run={dry_run}, limit={limit}, "
            f"seller_account_id={seller_account_id}, environment_type={environment_type}"
        )
        
        # Open database session using SessionManager
        with self.session_manager.session() as session:
            from src.notification.bootstrap import NotificationBootstrap
            from src.seller_env.bootstrap import SellerEnvironmentBootstrap
            from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository

            seller_env = SellerEnvironmentBootstrap.bootstrap(session)
            seller_resolver = seller_env["resolver"]
            
            ntf_repo = PersistentNotificationHistoryRepository(session)
            dispatcher = NotificationBootstrap.bootstrap(history_repo=ntf_repo, seller_resolver=seller_resolver)

            # Bootstrap Escalation Layer
            components = EscalationBootstrap.bootstrap(session, dispatcher)
            runner = components["runner"]

            # Run!
            enable_re_escalation = kwargs.get("enable_re_escalation", False)
            result = runner.run(
                db_session=session,
                dry_run=dry_run,
                seller_account_id=seller_account_id,
                environment_type=environment_type,
                enable_re_escalation=enable_re_escalation
            )
            return result
