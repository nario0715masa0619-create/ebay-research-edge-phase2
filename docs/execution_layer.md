# Phase H: Listing Readiness / Execution Layer

## 1. 目的と責務
Phase H は、Phase G で決定された Listing 候補（Candidate）を実際にプラットフォーム（eBay）へ出品・実行するためのレイヤーです。
Phase G (Listing Handoff / Execution Control Layer) では、候補のフィルタリングや重複抑止・容量制御などが行われますが、本 Phase H では、最終的な **出品の可否判定（Readiness）** と **APIを通じた実行（Execution）** に特化しています。

**mock/live unified interface の意義:** 
いきなり Live (本番環境) の API を叩くのではなく、抽象化された Gateway (Interface) を設けることで、Mock (スタブ・テスト環境) と Live (本番環境) を安全に切り替えることを可能にします。

## 2. 主要コンポーネント
- **ReadinessChecker**: 候補データが出品要件を満たしているかを検証しスコアリングするモジュール。
- **ExecutionPayload**: 実行に必要なデータを集約した不変なデータモデル。
- **ExecutionGateway**: 実行レイヤーのインターフェース。Mock / Live などの実装がここを継承する。
- **MockExecutor**: ExecutionGateway の Mock 実装。指定されたルール (Fixture) に従い成功・失敗をシミュレーションする。
- **ExecutionStateMachine**: 実行の各状態（準備完了、実行中、成功、失敗など）の安全な遷移と、その履歴を管理する。
- **ExecutionRetryManager**: 一時的なエラー（タイムアウト等）発生時の再試行スケジュールやバックオフを計算する。
- **ExecutionApplicationService**: 上記すべてのコンポーネントを統合し、Readiness -> State Machine -> Execution -> Persistence を制御するオーケストレーター。
- **ListingExecutionRunner**: Orchestrator (Job) から呼び出される処理のエントリポイント。
- **ExecutionAttemptRepository**: 実行履歴（attempt）をデータベースに保存・取得するためのリポジトリ。

## 3. readiness 判定
ReadinessChecker は 5 つの軸を評価し、スコア (0〜100) を算出します。
- `seller_valid`: 許可されたセラーか
- `sku_valid`: SKU が存在するか
- `content_complete`: タイトルなどの必須項目が揃っているか
- `pricing_valid`: 利益率が0を超えているか
- `state_clear`: 以前の実行がペンディング状態になっていないか

**判定基準:** スコアが **80以上** の場合のみ実行許可となります（Threshold = 80）。いずれかの軸で失格 (スコア低下) になった場合、例外（ReadinessThresholdNotMetError）等を通じて Hard Gate され、実行処理は即座に拒否されます。

## 4. execution payload
`ExecutionPayload` には以下の情報が含まれます。
- **必須フィールド**: `listing_id`, `seller`, `sku`, `bundle_state`, `market_eval`, `profitability_score`
- **コンテキスト**: `environment`, `dry_run`, `attempt_id`, `timestamp`

**from_listing() の役割**: 上流ドメインデータ (Candidate / Handoff) から ExecutionPayload への安全なマッピングを行います。
**secrets 禁止ルール**: 認証トークンやパスワード等の機密情報はペイロードに含めず、実行時（LiveExecutorなど）に環境変数や別のセキュアストアから解決する設計です。

## 5. gateway 方針
- **interface と mock/live 切替**: `ExecutionGateway` 抽象クラスを通じて切り替えます。
- **v0.1 は mock 主体**: 今回の実装は安全第一のため、まずは `MockExecutor` を主体として実装しています。
- **seller/environment guard**: `MockExecutor` や Live 版も、許可されたセラーID・環境 (`sandbox`/`production`) 以外ではバリデーションエラーとなります。
- **dry_run=true 時の扱い**: 副作用を伴わない (DBへの書き込みやAPI発火をしない) 動作を保証します。

## 6. state machine
- **state 一覧**: `ready_for_execution`, `executing`, `executed`, `failed`, `rolled_back`
- **許可遷移**: 
  - `ready_for_execution` -> `executing`
  - `executing` -> `executed` または `failed`
  - `executed` / `failed` -> `rolled_back`
- **invalid transition 扱い**: 許可されていない遷移は `InvalidStateTransitionError` として拒否されます。
- **audit append-only 方針**: 全ての状態遷移は `ExecutionTransition` オブジェクトとして記録され、監査用に履歴を取得できます。

## 7. retry / rollback / failure boundary
エラーの種類 (FailureBoundary) によって対応が変わります:
- **TIMEOUT / NETWORK_ERROR**: `retryable` (再試行可能)
- **UNKNOWN**: `retryable` (再試行上限付き)
- **SELLER_LIMIT**: `defer` (リトライではなく、上限緩和まで保留)
- **STATE_CONFLICT**: `non-retryable` / `cancel` (致命的エラー)

**バックオフ**: Exponential backoff で再試行間隔を決定。最大試行回数は 3 回。
**ロールバック**: 巻き戻しはあくまで「Execution Scope（この実行の取り消し）」に限定され、候補データそのものの破棄などは行いません。

## 8. DB 永続化
- **execution_attempts テーブル概要**: 1つの実行試行 (Attempt) ごとに1行のレコードを保存します。
- **主なカラム**: `attempt_id` (PK, ユニーク), `listing_id`, `seller_account_id`, `environment`, `status`, `payload_json`, `error_message`, `failure_boundary`, `retry_count`
- **unique/index 方針**: Idempotency (冪等性) を担保するため、`attempt_id` は必ずユニーク制約を持たせます。
- **Alembic revision**: `bb120efa3a17_add_execution_attempts_table.py` にてマイグレーションを管理。

## 9. 運用入口
- **CLI コマンド**: `src/listing_execution/cli.py` (`check-readiness`, `execute-listing`, etc.)
- **Web routes**: `src/listing_execution/web.py` (`/execution/readiness`, `/execution/execute`, etc.)
- **Orchestrator flow**: 既存のバッチ処理基盤に `ListingExecutionRunner` を登録。
これらはすべて「Thin Wrappers」として振る舞い、業務ロジックは全て `ExecutionApplicationService` に委譲されます。

## 10. 安全制御
- **seller/environment guard**: 未知の環境への誤出稿を防止します。
- **no silent success**: 重要な入力が欠損している場合に勝手に成功扱いせず、必ずエラーとします。
- **idempotency**: `attempt_id` ベースでの冪等性保証により、再送時の二重出品を防ぎます。
- **duplicate/retry distinction**: 再実行は常に新しい attempt として記録されます。
- **dry_run safe behavior**: 破壊的変更を行わないことを保証。
- **existing A–G non-impact**: 既存のフェーズ (A〜G) には一切の影響を与えません。

## 11. 既知の非スコープ
- **live executor**: 実際の eBay API 連携 (LiveExecutor) は Phase I にて実装されます。
- **listing 全体 rollback**: 全体を巻き戻すのではなく、あくまで Execution 層のステータスロールバックに留まります。
- **execution downstream / post-execution monitoring**: 出品後の監視・再出品フローなどは本フェーズの対象外です。
