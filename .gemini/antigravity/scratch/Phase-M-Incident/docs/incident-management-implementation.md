# Phase M: Incident Management / SLA & Ops Response Layer
## Implementation Overview

### 1. Introduction
Phase M introduces a comprehensive incident management system. It builds upon Phase K (SLA Policy & Observability) and Phase L (Operational Reporting) to orchestrate the lifecycle of incidents triggered by system failures and SLA breaches.

### 2. Architecture & Components
The incident management system is composed of several key layers:

*   **Models (DTOs & ORM)**: `Incident`, `IncidentEvent`, `IncidentLink`, `IncidentCandidate`, mapping to DB models (`IncidentModel`, `IncidentEventModel`, `IncidentLinkModel`).
*   **State Machine (`IncidentStateMachine`)**: Enforces strict transitions across the incident lifecycle: `OPEN -> ACKNOWLEDGED -> INVESTIGATING -> MITIGATED -> RESOLVED -> CLOSED` (plus `CANCELLED` and `REOPEN`).
*   **SLA Service (`IncidentSlaService`)**: Evaluates `ACK_OVERDUE`, `RESOLVE_OVERDUE`, and `BREACHED` states based on policy deadlines.
*   **Deduplication (`IncidentDeduplicationService`)**: Prevents alert storms by mapping recurring issues to existing open incidents.
*   **Management (`IncidentManagementService`)**: The core orchestrator handling all write actions, logging immutable `IncidentEvent` records for full audit trails.
*   **Presentation Layers**:
    *   **CLI (`admin_cli`)**: `ops incident list`, `show`, `dashboard` etc.
    *   **Web (`admin_web`)**: A Flask Blueprint providing visual dashboards, filtering, action forms, and detail views with colorful SLA badges.
*   **Orchestrator Jobs (`incident_jobs.py`)**: Asynchronous jobs for auto-detection, SLA evaluation, and daily overdue digests.
*   **Data Persistence (`repositories`)**: SQLAlchemy-based repository patterns (`IncidentRepositoryDB`, `IncidentEventRepositoryDB`, `IncidentLinkRepositoryDB`) to enforce read-write separation where needed and append-only semantics for events.

### 3. Database Schema
Three core tables were introduced via Alembic migration (`20260526_add_incident_tables.py`):
1.  `incidents`: Stores current state, SLA deadlines, metadata. Indexed on `opened_at`, `status`, `sla_state`, `seller`, `environment`.
2.  `incident_events`: Append-only table capturing state transitions, actors, notes, and timestamps for auditability.
3.  `incident_links`: Maps incidents to `attempt_id`, `listing_id`, `alert_id`, or `report_id`.

### 4. Verification & Testing
The system is thoroughly tested with over 150 automated test cases across Wave 1 to Wave 6. Testing covers state machine rules, deduplication logic, SLA computation, CLI/Web routing, and Database ORM constraints. All tests maintain a 100% pass rate.
