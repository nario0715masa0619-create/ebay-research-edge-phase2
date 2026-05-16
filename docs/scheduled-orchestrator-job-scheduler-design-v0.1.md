# Scheduled Orchestrator / Job Scheduler 設計書 v0.1

## 1. 目的
既存の Collection / Research / Listing Readiness / Listing Execution / Monitoring / Revise / Listing Sync / Recovery 各レイヤを、定期実行または手動起動可能なジョブとして束ねる運用オーケストレーション層を実装する。

## 2. ゴール
- 定期ジョブを宣言的に定義できる。
- 依存するジョブを順序制御（DAG）できる。
- 同時実行禁止ジョブを排他制御できる。
- JobRun と scheduler 実行履歴を統合し、トレーサビリティを確保する。
- 手動起動と定期起動の両方に対応する。

## 3. 主要コンポーネント

### 3.1 Orchestrator 層
- **`ScheduledOrchestrator`**: アプリ全体の実行入口。定期実行のポーリングや手動トリガーの受付を行う。
- **`SchedulerEngine`**: 実行対象ジョブの抽出、依存関係の解決、実行順序の決定を行うコアロジック。

### 3.2 ジョブ管理
- **`JobRegistry`**: システムに登録された `JobDefinition` を一括管理。
- **`JobDependencyResolver`**: `depends_on` 設定に基づき、実行グラフ（Topological Order）を構築。
- **`JobLockManager`**: 重複実行を防止するためのロック管理。

### 3.3 実行・集計
- **`JobDispatcher`**: 各ジョブの `target_runner` を特定し、実際の Pipeline / Gateway を呼び出す。
- **`JobResultAggregator`**: 各レイヤの独自リターン値を `ScheduledJobResult` へ標準化。

## 4. ジョブ定義 (JobDefinition)
| フィールド | 説明 |
| :--- | :--- |
| `job_name` | ユニークなジョブ名 |
| `schedule_type` | `interval`, `cron`, `manual_only`, `startup_once` |
| `interval_seconds` | 実行間隔（秒） |
| `depends_on` | 依存するジョブ名のリスト |
| `max_concurrency` | 同時実行数（通常 1） |
| `allow_overlap` | 重複実行の可否 |
| `target_runner` | 呼び出し対象の Pipeline / Gateway クラス名 |

## 5. 実行フロー例
1. **Source Collect**: アイテム収集
2. **Research**: 利益計算・スコアリング
3. **Listing Readiness**: 出品準備判定
4. **Listing Execution**: eBay 出品実行
5. **Monitoring / Revise**: 状態監視・改定
6. **Sync / Recovery**: 状態同期

## 6. 状態遷移
- `pending` -> `running` -> `completed` / `failed` / `skipped` / `timed_out`
- 依存ジョブが失敗した場合、後続は `skipped` される。

## 7. 永続化と監査
- すべての実行は `JobRun` に紐付けられ、詳細なメトリクス（processed, success, failed, etc.）が記録される。
- `CandidateEvidence` にもスケジューラ視点の決定事項を保存。
