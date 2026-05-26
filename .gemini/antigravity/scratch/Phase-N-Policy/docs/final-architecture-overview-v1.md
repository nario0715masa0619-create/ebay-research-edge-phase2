# Final Architecture Overview (v1)

## 1. Executive Summary
The eBay Research Edge (Phase2) system is a comprehensive, automated operations and policy management platform. It bridges the gap between incident detection, root cause analysis, policy enforcement, and safe configuration rollouts. Built on a modular Python architecture, it features robust CLI and Web interfaces, asynchronous background orchestration, and relational database persistence.

## 2. Core Components (Phase A-P)
- **Phase A-M**: Foundational layers including DB connectivity, eBay API integrations, notifications, and basic incident management.
- **Phase N (Ops Policy)**: Policy management, environment/seller overrides, automated policy candidate generation, and threshold tracking.
- **Phase O (Learning & Feedback)**: Root Cause Analysis (RCA) tracking, system learning, false signal detection, and automated recommendation generation based on resolved incidents.
- **Phase P (Change Management)**: Review queues, config versioning, rollout plans, and effective configuration precedence logic.

## 3. Data Models & Persistence
The system uses SQLAlchemy ORM and Alembic for schema migrations. Key tables include:
- `ops_policies`, `ops_policy_events`
- `learning_records`, `root_cause_analyses`, `learning_recommendations`
- `change_proposals`, `change_events`, `config_versions`, `rollout_plans`

## 4. Operations & CLI (Admin Tooling)
The `admin_cli` module provides a comprehensive suite of commands for operators. It supports formats like table, JSON, and CSV. Operators can propose changes, approve reviews, rollback plans, and inspect effective configurations directly from the terminal.

## 5. Web Dashboard (Admin UI)
The `admin_web` module (Flask/Jinja2) offers a visual dashboard for queue management. It includes timelines, impact analysis views, and review action buttons, enabling a non-technical oversight of the autonomous engine.

## 6. Background Orchestrator
Background jobs ensure the system is constantly evaluating state. Jobs run via standard orchestrators (like APScheduler):
- **Policy Jobs**: Threshold expiry, candidate generation.
- **Learning Jobs**: RCA clustering, false-positive digestion.
- **Change Mgmt Jobs**: Rollout validation, stale review cleanup.
All jobs are idempotent and support dry-runs.

## 7. Security & Access Control
The system enforces strict role-based access for critical actions (e.g., approving a ChangeProposal requires a different actor than the proposer). Audit trails are immutable and append-only (`ops_policy_events`, `change_events`).

## 8. Incident & Learning Lifecycle (Phase K-O)
Incidents are detected and resolved. The Learning engine digests these resolutions, generating Root Cause Analyses. If structural issues are found, it generates a `LearningRecommendation` to tune the system.

## 9. Change Management (Phase P)
Recommendations are transformed into `ChangeProposal`s. Upon human or consensus approval, they yield new `ConfigVersion`s. `RolloutPlan`s apply these configurations safely, evaluating global, environment, and seller-level precedence in real-time.
