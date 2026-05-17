# Escalation & Reminder Layer Design Spec v0.2

This document specifies the v0.2 extension of the Escalation/Reminder Layer. It introduces enterprise-grade incident management features including Service Level Agreement (SLA) breach tracking, re-escalation logic, aging visibility, route overriding, maintenance window suppression, operator notes, and bulk operational controls.

---

## 1. Objectives & Scope

### Purpose
To extend the v0.1 layer, providing deeper operational awareness and advanced rule engines. The goal is to track how long an issue has been open (Aging), whether it breached a critical timeframe (SLA), and dynamically escalate notifications again (Re-escalation) or suppress them during known outages (Maintenance Windows).

### Scope
1. **Re-escalation Engine**: Ability to re-escalate if a state remains open or breached past the initial escalation.
2. **SLA Tracking**: Explicit `sla_target_seconds` per policy. Exceeding this triggers a breach state, enabling severity/priority upgrades.
3. **Aging Visibility**: Compute `aging_seconds` and categorize into predefined buckets (e.g., `0_15m`, `24h_plus`).
4. **Maintenance Windows**: Ability to suppress reminders/escalations for specific environments/sellers during known downtimes.
5. **Route Overrides**: Dynamic notification routing based on SLA breach, seller account, and environment.
6. **Bulk Operations**: Bulk Ack/Resolve/Silence actions.
7. **Notes & Timeline**: Operator annotations attached to states, visualized in a unified timeline.

---

## 2. Domain & DB Architecture (v0.2 additions)

### EscalationPolicy (Extended)
* `policy_version`: int
* `re_escalation_enabled`: bool
* `re_escalation_interval_seconds`: int | None
* `re_escalation_max_count`: int | None
* `sla_target_seconds`: int | None
* `sla_breach_severity`: str | None
* `sla_breach_priority`: str | None
* `maintenance_window_respected`: bool
* `bulk_action_enabled`: bool
* `route_override_key`: str | None

### EscalationState (Extended)
* `aging_seconds`: int | None
* `aging_bucket`: str | None
* `sla_target_seconds`: int | None
* `sla_breached_at`: datetime | None
* `sla_breach_count`: int
* `re_escalation_count`: int
* `last_re_escalated_at`: datetime | None
* `maintenance_suppressed_until`: datetime | None
* `latest_note_at`: datetime | None
* `latest_note_by`: str | None
* `route_snapshot_json`: dict | None
* `incident_key`: str | None

### New Entities
1. **EscalationNote**: Operator annotations (state_id, body, author, timestamp).
2. **MaintenanceWindow**: Downtime periods (seller_account_id, environment_type, event_type, starts_at, ends_at).

---

## 3. Core Engine Components

1. **Aging & SLA Calculators**: Evaluated continuously against `first_seen_at`.
2. **ReEscalationDecisionEngine**: Decides if a previously escalated state requires another push.
3. **MaintenanceWindowService**: Resolves active windows and determines if the current evaluation is suppressed.
4. **RouteResolver**: Determines final notification endpoints factoring in overrides and Sandbox constraints.
5. **BulkActionService**: Wraps Ack/Silence/Resolve in iterative batches.
6. **TimelineBuilder**: Merges transitions and notes into a unified chronology.

---

## 4. Maintenance & Suppression Logic

If an active `MaintenanceWindow` overlaps with the current evaluation time, actions (reminder, escalation) are paused. State records are still updated (e.g. aging), but notifications are suppressed until the window ends.

---

## 5. Implementation Strategy

1. **DB Updates**: Add schema models in `src/db/models.py` and run Alembic `revision --autogenerate`.
2. **Domain Models**: Update `src/escalation/models.py`.
3. **New Logic Modules**: Implement `sla.py`, `aging.py`, `re_escalation_decision_engine.py`, etc.
4. **Integration**: Update Web (templates, routes), CLI, and the Scheduled Orchestrator Job definition.
5. **Tests**: Ensure backwards compatibility with v0.1 tests and add coverage for new engines.
