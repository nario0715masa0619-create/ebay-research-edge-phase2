# Phase L: Operational Reporting & Export Layer Implementation

This document provides a comprehensive overview of the Phase L architecture, implementation details, and features added to the Operational Reporting & Export Layer.

## Overview

The Operational Reporting & Export Layer (Phase L) provides visibility into the automated execution state of the platform without exposing system secrets or allowing state modification. It is designed around the principles of "read-only access" and "append-only safety".

### Key Components

1. **DTOs (Data Transfer Objects)**: Define strict schemas for cross-layer data exchange (e.g., `ReportDTO`, `DailyExecutionSummaryDTO`).
2. **Services**: Pure Python logic wrapping data queries (mocked in this phase) to provide reporting and analysis points for CLI, Web, and Jobs.
3. **Admin CLI (`ops report`)**: Allows operators to query reporting data in standard output formats (`table`, `json`, `csv`) and trigger downloads.
4. **Admin Web (`Flask Web App`)**: Provides a user-friendly read-only dashboard to filter and view summaries, alerts, failures, and seller health.
5. **Orchestrator Jobs**: Schedulable cron-like jobs for generating routine reports (e.g., daily summaries, failure digests).
6. **Artifact Storage**: A DB and file-backed repository for preserving generated reports safely for long-term audit purposes.

## Storage Architecture (Wave 6)

In Wave 6, we implemented persistent storage for report artifacts.

### DB Schema (`report_artifacts`)
- **Primary Key**: `report_id` (UUID)
- **Metadata**: `report_type`, `format`, `row_count`, `generated_at`, `generated_by`, `trigger_source`
- **Soft Deletion**: `is_deleted` flag
- **Expiry**: `expires_at` timestamp
- **File Reference**: `file_path` (local storage path) and `blob_ref` (cloud storage reference placeholder)

### Migration
Alembic is configured with autogenerate capabilities, and the `1a2b3c4d5e6f_add_report_artifacts_table.py` revision handles the upgrade and downgrade logic for SQLite/PostgreSQL.

## Endpoints and Commands

### CLI Commands (`ops report`)
- `summary`: Get execution summaries.
- `failure-digest`: View recent failure counts.
- `alert-digest`: View alert timelines.
- `seller-health`: Evaluate listing status for a specific seller.
- `env-health`: Analyze health by environment.
- `audit-export`: Export raw audit logs.
- `artifacts`: List stored artifacts.
- `show --report-id <id> [--download]`: View or download a specific artifact.

### Web Routes
- `GET /execution/reports`: Main list view.
- `GET /execution/reports/summary`: Summary preview.
- `GET /execution/reports/failures`: Failure digest preview.
- `GET /execution/reports/alerts`: Alert digest preview.
- `GET /execution/reports/sellers`: Seller health report.
- `GET /execution/reports/artifacts/<report_id>/download`: Direct file download.

## Error Handling & Resiliency

1. **Service Layer Validation**: Validates `from_date` and `to_date` ranges; raises `ValueError`.
2. **Orchestrator Retries**: Wraps job executions to allow up to 3 retries upon transient failures before marking the job as `failed`.
3. **Artifact Expiry**: Implemented checks at the download endpoints (`410 Gone` for expired files, `404 Not Found` for missing or soft-deleted items).
4. **Dry Run Support**: Operations support `dry_run=True` to mock execution flow without polluting the artifact DB or disk storage.

## Conclusion
Phase L is now formally completed, establishing a robust, read-only analytics foundation that bridges system execution metrics to platform operators securely.
