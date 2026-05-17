import logging
from typing import List, Dict, Any
from .models import NotificationEvent, NotificationRule, NotificationDispatchResult, NotificationBatchResult
from .rule_engine import NotificationRuleEngine
from .deduper import NotificationDeduper
from .cooldown import NotificationCooldownManager
from .channel_registry import NotificationChannelRegistry

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    def __init__(self, rule_engine: NotificationRuleEngine, deduper: NotificationDeduper, cooldown_manager: NotificationCooldownManager, channel_registry: NotificationChannelRegistry, seller_resolver = None):
        self.rule_engine = rule_engine
        self.deduper = deduper
        self.cooldown_manager = cooldown_manager
        self.channel_registry = channel_registry
        self.history_repo = None # Injected via bootstrap
        self.classifier = None # Injected via bootstrap
        self.seller_resolver = seller_resolver

    def notify(self, event: NotificationEvent, dry_run: bool = False, bypass_checks: bool = False) -> NotificationBatchResult:
        if self.classifier:
            self.classifier.classify(event)
        return self.dispatch(event, dry_run=dry_run, bypass_checks=bypass_checks)

    def dispatch(self, event: NotificationEvent, dry_run: bool = False, bypass_checks: bool = False) -> NotificationBatchResult:
        batch = NotificationBatchResult()
        
        # 1. Resolve rules
        rules = self.rule_engine.resolve_rules(event)
        if not rules:
            logger.debug(f"No rules matched for event {event.event_type}")
            return batch
            
        # 2. Collect targets
        dispatches = []
        seen_channels = set()
        for rule in rules:
            # Check dedupe/cooldown per rule if needed, or globally
            if not bypass_checks:
                if self.deduper.should_dedupe(event, window_override=rule.dedupe_window_seconds):
                    batch.deduped_count += 1
                    logger.debug(f"Event {event.event_type} deduped by rule {rule.rule_name}")
                    continue

                if self.cooldown_manager.is_cooling_down(event, cooldown_override=rule.cooldown_seconds):
                    batch.skipped_count += 1
                    logger.debug(f"Event {event.event_type} skipped due to cooldown in rule {rule.rule_name}")
                    continue
                
            channels = rule.channel_targets
            if self.seller_resolver and event.seller_account_id:
                from src.seller_env.notification_resolver import SellerNotificationRouteResolver
                route_resolver = SellerNotificationRouteResolver(self.seller_resolver)
                channels = route_resolver.resolve_channels(event, channels)

            for channel in channels:
                if channel not in seen_channels:
                    dispatches.append((channel, rule))
                    seen_channels.add(channel)
                
        # 3. Dispatch to channels
        for channel_name, rule in dispatches:
            batch.processed_count += 1
            
            if dry_run or (rule.only_when_not_dry_run and dry_run):
                res = NotificationDispatchResult(
                    event_id=event.event_id,
                    channel_name=channel_name,
                    dispatch_status="skipped",
                    skipped_reason="dry_run",
                    success_flag=True
                )
                batch.skipped_count += 1
            else:
                notifier = self.channel_registry.get_notifier(channel_name)
                if not notifier:
                    res = NotificationDispatchResult(
                        event_id=event.event_id,
                        channel_name=channel_name,
                        dispatch_status="failed",
                        error_summary=f"Notifier for channel {channel_name} not found",
                        success_flag=False
                    )
                    batch.failed_count += 1
                else:
                    try:
                        res = notifier.send(event)
                        if res.success_flag:
                            batch.dispatched_count += 1
                            self.cooldown_manager.mark_dispatched(event)
                        else:
                            batch.failed_count += 1
                    except Exception as e:
                        res = NotificationDispatchResult(
                            event_id=event.event_id,
                            channel_name=channel_name,
                            dispatch_status="failed",
                            error_summary=str(e),
                            success_flag=False
                        )
                        batch.failed_count += 1
            
            batch.results.append(res)
            self._record_history(event, res)
            
        return batch

    def _record_history(self, event: NotificationEvent, res: NotificationDispatchResult):
        if self.history_repo:
            try:
                self.history_repo.save_dispatch(event, res)
            except Exception as e:
                logger.error(f"Failed to record notification history: {e}")
