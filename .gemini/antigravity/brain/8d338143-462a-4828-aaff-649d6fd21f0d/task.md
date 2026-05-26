# Phase M / Incident Management / SLA & Ops Response Layer

## Wave 1 Tasks
- [x] Incident / IncidentEvent / IncidentLink DTO 定義
- [x] SlaPolicy / SlaEvaluationResult / IncidentCandidate DTO 定義
- [x] IncidentStateMachine 実装
- [x] IncidentSlaService 実装
- [x] テスト追加（25件以上）
- [x] pytest 実行
- [x] Wave 1 開始・完了マーク
- [x] git commit & push

## Wave 2 Tasks
- [x] IncidentDetectionService 実装
- [x] IncidentDeduplicationService 実装
- [x] IncidentLinkingService 実装
- [x] IncidentCandidate evaluation ロジック
- [x] テスト追加（25件以上）
- [x] pytest 実行
- [x] Wave 2 完了マーク
- [x] git commit & push

## Wave 3 Tasks
- [x] IncidentManagementService 実装
- [x] IncidentDashboardService 実装
- [x] IncidentDigestService 実装
- [x] テスト追加（25件以上）
- [x] pytest 実行
- [x] Wave 3 完了マーク
- [x] git commit & push

## Wave 4 Tasks
- [x] CLI incident commands 実装
- [x] テスト追加（20件以上）
- [x] pytest 実行
- [x] Wave 4 完了マーク
- [x] git commit & push

## Wave 5 Tasks
- [x] Web incident routes 実装
- [x] Web templates 実装
- [x] テスト追加（20件以上）
- [x] pytest 実行
- [x] Wave 5 完了マーク
- [x] git commit & push

## Wave 6 Tasks (Final)
- [x] incident 系テーブル設計 + migration 作成
- [x] IncidentModel / IncidentEventModel / IncidentLinkModel ORM 実装
- [x] IncidentRepository DB実装
- [x] IncidentEventRepository DB実装
- [x] IncidentLinkRepository DB実装
- [x] Orchestrator incident jobs 実装
- [x] テスト追加（25件以上）
- [x] pytest 全体実行
- [x] docs/incident-management-implementation.md 作成
- [x] Phase M 完了マーク
- [x] git commit & push

## Phase N: Operations Policy & Control Layer
### Wave 1 Tasks
- [x] OpsPolicy / OpsPolicyEvent DTO
- [x] EffectivePolicyDecision / OpsPolicyCandidate DTO
- [x] OpsPolicyStateMachine 実装
- [x] OpsPolicyPrecedenceService 実装
- [x] EffectivePolicyService 実装
- [x] pytest 31件以上実行・100%パス
- [x] task.md / walkthrough.md 更新
- [x] git commit & push

### Wave 2 Tasks
- [x] IncidentToPolicyCandidateService 実装
- [x] IncidentDetectionService 実装
- [x] テスト追加（25件以上）
- [x] task.md / walkthrough.md 更新
- [x] git commit & push

### Wave 3 Tasks
- [x] OpsPolicyManagementService 実装
- [x] OpsPolicyDashboardService 実装
- [x] OpsPolicyDigestService 実装
- [x] テスト追加（30件以上）
- [x] task.md / walkthrough.md 更新
- [x] git commit & push

### Wave 4 Tasks
- [x] CLI コマンド (12+) 実装
- [x] テスト追加（20件以上）
- [x] task.md / walkthrough.md 更新
- [x] git commit & push

### Wave 5 Tasks
- [ ] Web routes (6+) 実装
- [ ] Jinja2 templates (6) 実装
- [ ] テスト追加（20件以上）
- [ ] task.md / walkthrough.md 更新
- [ ] git commit & push
