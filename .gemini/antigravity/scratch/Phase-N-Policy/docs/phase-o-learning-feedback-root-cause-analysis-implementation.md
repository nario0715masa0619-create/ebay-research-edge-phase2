# Phase O Implementation: Learning, Feedback, and Root Cause Analysis (RCA)

## Overview
Phase O introduces the Learning and Feedback Loop, bringing autonomous improvement capabilities to the Operations Policy system. It captures insights from resolved incidents and policy actions, analyzes recurring issues and false signals, and generates actionable recommendations to improve detection thresholds, policy configurations, and system design.

This module closes the loop between Operations (Phase N) and System Configuration, ensuring that knowledge is captured structurally rather than remaining tacit among human operators.

## Use Cases Covered
1. **Candidate Generation**: Auto-scan resolved incidents and policy actions to propose learning candidates.
2. **RCA Recording**: Capture structured Root Cause Analysis for a candidate.
3. **Recommendation Lifecycle**: Propose, review, approve, and implement system improvements based on RCA.
4. **Effectiveness Evaluation**: Measure the real-world impact of policies on incident resolution times and recurrence.
5. **Recurring Issue Analysis**: Cluster similar incidents to identify systemic flaws.
6. **False Signal Detection**: Analyze false positives/negatives to recommend threshold adjustments.
7. **Dashboard & Summaries**: Present learning metrics to operators.
8. **CLI Management**: Full control over learning records via CLI.
9. **Web Interface**: Browser-based management with visual dashboards.
10. **Automated Jobs**: Nightly and weekly jobs to scan candidates, evaluate effectiveness, and detect stale backlog.
11. **Persistence**: Store all learning data in a relational database using SQLAlchemy/Alembic.
12. **Idempotency**: Safe, repeatable background jobs.
13. **Append-only History**: Immutable timestamps for RCA creation to ensure auditability.

## Architecture
The system follows a standard layered architecture:
- **Models**: `LearningRecord`, `RootCauseAnalysis`, `LearningRecommendation`, `LearningCandidate` (DTOs and ORM Models)
- **Repositories**: `LearningRecordRepository`, `RootCauseAnalysisRepository`, `LearningRecommendationRepository`
- **Services**: 
  - Core: `LearningRecordService`, `RootCauseAnalysisService`
  - Lifecycle: `LearningRecommendationService`, `LearningCandidateService`
  - Analytics: `LearningDashboardService`, `RecurringIssueAnalysisService`, `FalseSignalAnalysisService`, `LearningEffectivenessService`
- **Interfaces**: CLI (`learning_commands.py`) and Web (`learning_routes.py`)
- **Orchestration**: Background Jobs (`learning_jobs.py`)

## Models & DB Schema
Three core tables were introduced via Alembic migration:
- **`learning_records`**: Central entity linking incidents, policies, and RCA. Contains fields for impact scope, effectiveness rating, and false signal flags.
- **`root_cause_analyses`**: Append-only records storing the "5 Whys" (problem, symptom, cause, contributing factors) and proposed prevention.
- **`learning_recommendations`**: Trackable action items with a state machine (`proposed` -> `under_review` -> `approved` -> `implemented`).

## Integration Points
- **Phase K/L (Incidents & Detection)**: Reads incident data to find candidates and analyzes false signals against detection thresholds.
- **Phase M/N (Policies & Operations)**: Evaluates policy effectiveness and links learning records to specific applied policies.
- **Future Phases**: Output from `LearningRecommendation` serves as direct input to future auto-remediation and rule rewriting engines.

## Safety Controls
- **Human-in-the-Loop**: Recommendations require explicit approval before implementation.
- **Dry-run**: All background jobs support a `dry_run` flag to preview analysis without persisting state.
- **Immutable Timestamps**: Core timestamps (`created_at`) are locked to prevent historical tampering.

## Future Extensions
- ML-driven autonomous improvement (predictive candidate generation).
- Automatic rule rewriting based on approved recommendations.
- Connection to external knowledge bases.
- Auto postmortem generation.
