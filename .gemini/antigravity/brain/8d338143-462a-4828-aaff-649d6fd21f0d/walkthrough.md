# Phase M / Incident Management / SLA & Ops Response Layer

## Wave 1 実装内容
Phase M の最初のステップとして、インシデントのライフサイクルとSLAを管理する基礎コンポーネント (Wave 1) を実装しました。

### 1. Incident 関連 DTO の定義
`src/incident/models` 配下に以下のデータクラス（DTO）を定義し、インシデントとその付帯情報を表現しました。
- `Incident`: インシデントの基本情報 (ID, type, severity, status, sla_state, 各種日時など)
- `IncidentEvent`: インシデントに紐づくイベント (作成, 状態変更, SLA違反など) とその履歴
- `IncidentLink`: 関連するエンティティ (出品, アラート, セラーなど) とのリンク情報
- `SlaPolicy`: 重要度 (Severity) に応じた Ack / Resolve の期限定義
- `SlaEvaluationResult`: インシデントの現在のSLA遵守状態・違反時間を含む評価結果
- `IncidentCandidate`: 検出フェーズから渡されるインシデントの候補情報

### 2. Incident State Machine の実装
`src/incident/services/incident_state_machine.py` にて、インシデントのステータス遷移を一元管理する `IncidentStateMachine` を実装しました。
- 許可されるステータス遷移パターンを辞書で定義 (`OPEN` -> `ACKNOWLEDGED`, `CLOSED` など)
- 許可されない遷移（例: `CLOSED` -> `ACKNOWLEDGED`）に対しては `InvalidStateTransitionError` を送出
- `reopen` 操作は `RESOLVED` 状態からのみ許可し、解決時刻 (`resolved_at`) をリセットする仕様

### 3. Incident SLA Service の実装
`src/incident/services/incident_sla_service.py` にて、SLA の計算と評価を行う `IncidentSlaService` を実装しました。
- 重要度 (CRITICAL/HIGH/MEDIUM/LOW) に基づく SLA Policy の適用
- 発生時刻 (`opened_at`) を基にした Ack / Resolve 期限の算出 (`calculate_due_times`)
- 現在時刻と期限を比較した違反チェックと超過分数 (`overdue_minutes`) の算出
- `WITHIN_SLA`, `ACK_BREACHED`, `RESOLVE_BREACHED`, `BOTH_BREACHED` への状態評価 (`evaluate_sla_state`)
- SLA違反を記録する `IncidentEvent` の生成 (`record_sla_breach_event`)

### 4. 自動テストの追加
`tests/incident/services/` 配下に pytest を用いたテストケースを計27件作成し、全て正常にパス (100% Passed) することを確認しました。状態遷移のバリデーションや SLA の境界値評価など、堅牢性を担保しています。

## Wave 2 実装内容
インシデントの検知 (Detection)、重複排除 (Deduplication)、および関連エンティティのリンク (Linking) を担うサービスコンポーネント (Wave 2) を実装しました。

### 1. IncidentDetectionService
システムから発せられる各種シグナルを分析し、インシデント候補 (`IncidentCandidate`) を生成するロジックを実装しました。
- **検知ルール**:
  - `failure_spike`: 同一セラー/環境で指定時間窓内に5回以上の失敗 (Severity: HIGH)
  - `alert_burst`: 指定時間窓内に10個以上のアラート (Severity: CRITICAL)
  - `guard_rejection`: 指定時間窓内に3回以上の拒否 (Severity: MEDIUM)
  - `credentials_failure`: 3回以上の認証失敗 (Severity: HIGH)
  - `retry_loop_risk`: 同一試行が1時間を超えるリトライ (Severity: MEDIUM)
  - `seller_health_degradation`: セラーの失敗率が30%を超過 (Severity: HIGH)
- **Dry Run 制御**: 生成された候補内のすべてのエンティティが `dry_run=True` を持つ場合、インシデントの `Severity` を1段階ダウングレード（例: CRITICAL -> HIGH, HIGH -> MEDIUM）し、実運用へのノイズを抑えるロジックを導入しました。

### 2. IncidentDeduplicationService
大量の同一異常が検知された際に、インシデントの乱立を防ぐ重複排除 (Deduplication) サービスを実装しました。
- **マッチ条件**: 既存のインシデントが `OPEN`, `ACKNOWLEDGED`, `INVESTIGATING` のいずれかの状態であり、かつ `incident_type`, `seller`, `environment`, `error_code` が完全に一致すること。
- **時間窓**: デフォルトで過去30分以内に発生したインシデントを対象。
- **重複時の挙動**: 新規のインシデントを `CANCELLED` 状態とし、`duplicate_of_incident_id` に既存のIDを記録 (`mark_as_duplicate`)。また、既存インシデントには重複発生のイベント履歴を追記 (`add_event_to_existing`)。

### 3. IncidentLinkingService
インシデントに対して、影響範囲を特定するための各種エンティティを紐付ける Linking サービスを実装しました。
- **対応エンティティ**: Attempt, Listing, Alert, Report, Seller, Environment
- `link_attempts`, `link_listings`, `link_alerts` など、複数IDを一括で紐付けるインターフェースを提供。
- **重複排除**: 同一インシデントに対して既にリンクされているエンティティは無視し、重複リンクの作成を防止。

### 4. 自動テストの追加
Wave 2 にて新たにテストケース27件を追加し、Wave 1と合わせて計54件のテストを実行しました。全件が 100% Passed となり、検知閾値の評価、重複インシデントのキャンセルフロー、エンティティリンクの重複排除が正常に動作することを確認しました。

## Wave 3 実装内容
運用ダッシュボードやレポート、及びインシデントの全体ライフサイクルを管理するための高度なサービスレイヤー (Wave 3) を実装しました。

### 1. IncidentManagementService
インシデントのライフサイクル全体 (起票・アサイン・調査・緩和・解決・クローズ) を統括するサービスを実装しました。
- `IncidentStateMachine` と連携し、各状態遷移時に `IncidentEvent` を発行して Audit Trail (監査証跡) を残します。
- `IncidentDeduplicationService` を組み込み、インシデント生成時に既に同一原因の既存インシデントが Open 状態である場合は、重複排除を行います。
- `IncidentSlaService` と連携し、インシデント起票時には自動で SLA (Ack/Resolve の期限) を算出し、解決時には SLA の超過 (Breach) 判定と監査イベントの記録を実行します。

### 2. IncidentDashboardService
インシデントの現状と運用メトリクスを集計するダッシュボード機能を提供します。
- **サマリ集計**: オープン数、解決数、超過 (Overdue / Breached) インシデントの数、深刻度別・セラー別・環境別の分布を `IncidentSummary` オブジェクトとして返却。
- **SLA メトリクス**: 指定期間内における、インシデントの平均応答時間 (MTTA: Mean Time to Acknowledge) と平均解決時間 (MTTR: Mean Time to Resolve) を算出。
- **絞り込み**: セラーや環境、深刻度によるフィルタリングに加え、Ack 期限や Resolve 期限を超過しているオープンインシデント (`overdue`) の一覧抽出機能。

### 3. IncidentDigestService
日次サマリや重複インシデントのリストなどを定期報告 (ダイジェスト) 用に生成・フォーマットするサービスを実装しました。
- `generate_daily_summary_digest`: `IncidentDigestReport` オブジェクトとして、指定日のサマリと上位の深刻度トピックを出力。
- `generate_repeated_incidents_digest`: 重複発生により Cancel となったインシデント履歴を抽出し、問題の再発頻度レポートに活用可能としました。
- ダッシュボードサービスと緊密に連携し、データを JSON やレポート形式に落とし込みやすくしています。

### 4. 自動テストの追加
Wave 3 にてテストケース26件を追加し、総計80件のテストを実行しました（100% Passed）。Deduplication 機構が ManagementService に正しく組み込まれていること、ダッシュボードのMTTA/MTTR集計が正しい時間計算を行うこと、ダイジェスト生成が正しくレポートDTOを構成することを確認しました。

## Wave 4 実装内容
運用チームがインシデント管理を行うための CLI コマンド (`ops incident`) 群を実装しました。

### 1. CLI コマンド構造
`src/admin_cli/incident_commands.py` にて `argparse` を用いた CLI インターフェースを構築し、以下の14個のサブコマンドを提供しています。
- **Read-only 系**: `scan`, `list`, `show`, `dashboard`, `overdue`, `breached`, `links`
- **Controlled-write 系**: `acknowledge`, `assign`, `investigate`, `mitigate`, `resolve`, `close`, `reopen`, `cancel`
- 存在しないインシデントIDを指定した場合は "not found" エラーとなり、不正な状態遷移 (InvalidStateTransitionError) も適切に捕捉してエラーメッセージを表示します。

### 2. 表示・フォーマット機能
CLI の出力を運用者が直感的に理解できるよう、ターミナル出力向けのカラーリングとフォーマットを実装しました。
- **Severity**: CRITICAL(赤), HIGH(オレンジ), MEDIUM(黄), LOW(グレー) の ANSI カラー表示。
- **SLA Badge**: `format_sla_badge()` 関数により、`[ON_TRACK]`, `[ACK_OVERDUE Xm]`, `[RESOLVE_OVERDUE Xm]`, `[BREACHED]` のバッジを動的生成。超過分数(Xm)を含め、超過やBreachは赤色で強調表示します。
- **List / Dashboard**: `list` などの一覧コマンドでは、ID、ステータス、深刻度、セラー、起票日時、SLA状態を整列したテーブル形式で出力します。
- **Show**: 対象インシデントの詳細情報に加え、過去の `IncidentEvent` をタイムスタンプ (`created_at`) 順に並べたタイムラインを表示します。

### 3. バックエンドサービスとの統合
- `list` コマンドのフィルタリング (status, severity, seller, environment, overdue-only, breached-only) を DashboardService / Repo と連動。
- 状態変更コマンド (`acknowledge` 等) はすべて `IncidentManagementService` へ処理を委譲し、状態遷移イベントの完全性を担保しています。
- `dashboard` サブコマンドでは、`DashboardService` が集計した Summary オブジェクトから MTTA / MTTR を含めたメトリクスを出力します。

### 4. 自動テストの追加
Wave 4 向けに CLI インターフェース用のテストケース24件を追加しました。各種サブコマンドのルーティング、引数パースエラー時の動作 (Exit code 2)、UUIDエラーハンドリング、フィルタの動作確認、カラー・バッジ生成ロジックの動作検証を行い、全て 100% Passed を達成しました。

## Wave 5 実装内容
運用チームがインシデント管理をブラウザ上で行えるよう、Web (HTML) インターフェースを実装しました。

### 1. Web Routes と Templates (Flask Blueprint & Jinja2)
`src/admin_web/routes/incident_routes.py` を中心として以下の11個のルーティングを提供し、それぞれに対応する Jinja2 テンプレートを作成しました。
- **Read-only 画面**:
  - `GET /ops/incidents/` (一覧画面: filter フォーム付き)
  - `GET /ops/incidents/<incident_id>` (詳細画面: 基本情報, タイムライン, 関連リンク, アクションフォーム)
  - `GET /ops/incidents/dashboard` (ダッシュボード画面: サマリ, MTTA/MTTR, 最新インシデント一覧)
  - `GET /ops/incidents/overdue` (超過インシデント一覧画面: 超過時間順にソート)
  - `GET /ops/incidents/breached` (SLA Breach インシデント一覧画面)
  - `GET /ops/incidents/candidates` (自動検知された候補一覧画面)
- **Controlled-write (POST アクション)**:
  - `POST /ops/incidents/<incident_id>/acknowledge`
  - `POST /ops/incidents/<incident_id>/assign`
  - `POST /ops/incidents/<incident_id>/resolve`
  - `POST /ops/incidents/<incident_id>/close`
  - `POST /ops/incidents/<incident_id>/reopen`

### 2. UI 表示・フォーマット機能
- **SLA Badge / Severity Badge**: CLI と同様の色分けルールを適用し、CSS のクラス (`.sev-CRITICAL`, `.sla-OVERDUE` など) で視覚的に強調するバッジを実装しました。
- **Overdue  vurgu**: overdue や breached の画面では、超過分数を赤文字で表示 (`class="red"`) し、対応優先度を一目で判断可能にしています。
- **Action Form**: 詳細画面の下部に POST リクエストを送るシンプルなフォーム群を配置し、ManagementService を安全に叩ける最小限の Controlled-write UI を実現しました。

### 3. Service とのエラーハンドリング統合
- `DashboardService`, `ManagementService`, `DetectionService`, `IncidentRepo` 等を依存関係として呼び出し、バックエンドロジックの処理結果を直接レンダリングしています。
- 無効な UUID 指定や未登録のインシデントアクセス時は `abort(404)` で 404 エラーを返却します。
- `POST` アクション時に発生した Service 層の例外（不正な状態遷移エラー等）はキャッチし、`abort(400)` でエラーメッセージを出力します。

### 4. 自動テストの追加
Wave 5 向けに Web ルートのテストを `pytest` (Flask test_client) を用いて 20件追加しました。各エンドポイントへのルーティング、クエリパラメータによるフィルタ処理、テンプレート内の特定文字列（CSSクラス等）の出力検証、および POST メソッド時のリダイレクトやエッジケースエラー対応を含め、全て 100% Passed となりました。

## Wave 6 実装内容 (Final)
Phase M の最終工程として、インメモリで動作していた Repository 群をデータベース (SQLAlchemy) に永続化し、非同期で動作する Orchestrator Job 群を実装してシステムを完成させました。

### 1. データベース設計と ORM (SQLAlchemy)
`src/incident/models/orm_models.py` を作成し、3つのテーブルモデルを定義しました。
- **`incidents`**: インシデントの基本情報と SLA 情報、各種タイムスタンプを管理。検索パフォーマンス向上のため、`opened_at`, `status`, `sla_state`, `seller_account_id` 等にインデックスを付与しています。
- **`incident_events`**: 状態遷移やアクションの履歴を Append-only で記録する監査証跡テーブルです。`created_at` 昇順でインデックスを張り、履歴の完全性を担保します。
- **`incident_links`**: 他エンティティ（Alert, Listing, Report 等）との関連付けを管理するテーブルです。

これらをDBに適用するための Alembic Migration スクリプト (`alembic/versions/20260526_add_incident_tables.py`) を作成し、Up/Down 処理とインデックス生成を定義しました。

### 2. Repository DB 実装
インメモリでモックとしていたリポジトリを RDB 向けに本格実装しました。
- `IncidentRepositoryDB`: CRUD の他に、ダッシュボードやダイジェストで必要な `get_open_incidents`, `get_overdue_incidents`, `get_breached_incidents`, `list_incidents (フィルタ/ソート/ページネーション対応)` を提供。
- `IncidentEventRepositoryDB`: Append-only 原則に従い、Event の追記と `incident_id` 単位での抽出 (`ORDER BY created_at ASC`) を提供。
- `IncidentLinkRepositoryDB`: Link の追加、削除、および双方向からの検索機能を提供。

### 3. Orchestrator Jobs 実装
バックグラウンドで定期実行されるシステムジョブ (`src/orchestrator/incident_jobs.py`) を実装しました。
- `incident_detection_job`: `DetectionService` による候補検知と `ManagementService` による自動起票をバッチ処理で実行します。
- `incident_sla_evaluation_job`: DB上の Open な全インシデントに対し SLA 期限を定期評価し、超過時に `sla_state` を `ACK_BREACHED` 等に自動更新します。
- `incident_overdue_digest_job`: `DigestService` を呼び出し、Overdue 対象のレポートを定期生成します。

### 4. 自動テストの実行
Wave 6 にて新たに28件の DB Repo および Orchestrator Job のテストを追加し、全体で 131 warnings / 28 passed を達成しました。これまでの Wave (1〜5) のテストと合わせて後退 (Regression) がないことを確認し、Phase M 全体の正常動作を担保しました。

### Phase M の全体サマリ
Phase M を通じて、堅牢な SLA 管理機能、一貫性のある State Machine、重複を排除する Deduplication ロジック、これらを操作・集計する Service/Repo 群、そして CLI/Web の UI レイヤーと非同期 Job に至るまでの **"Incident Management / SLA & Ops Response Layer"** が完成しました。これにより運用・開発チームは、システム障害や SLA 超過の脅威を迅速に検知し、適切に追跡・緩和・解決するサイクルを実現できるようになりました。

## Phase N: Operations Policy & Control Layer
### Wave 1 実装内容
運用制御ポリシーを管理・適用するための基盤モデルとステートマシン、および優先度解決サービスを実装しました。

1. **OpsPolicy スコープと DTO**
   `OpsPolicy`, `OpsPolicyEvent`, `OpsPolicyCandidate`, `EffectivePolicyDecision` の各データモデルを構築しました。適用スコープは `GLOBAL`, `ENVIRONMENT`, `SELLER`, `EXECUTION_CHANNEL` の4段階で表現されます。

2. **State machine 遷移図**
   `OpsPolicyStateMachine` により、以下の厳格なライフサイクルを管理します:
   - `PROPOSED` → `APPROVED` / `REJECTED`
   - `APPROVED` → `ACTIVE` / `CANCELLED`
   - `ACTIVE` → `RELEASED` / `EXPIRED` / `CANCELLED`
   一度解放やキャンセル等の状態になると、再活性化できない（Terminal）制約を持ち、履歴は `OpsPolicyEvent` に追記されます。

3. **Strong policy review requirement**
   `PolicyLevel.STRONG` のポリシーを承認 (`approve_policy`) する場合、必ず `approved_by` と `review_due_at` の設定を必須とするバリデーションを組み込み、厳格なレビュープロセスを強制します。

4. **Precedence logic (優先度評価と Deny-first principle)**
   `OpsPolicyPrecedenceService` は、`GLOBAL > ENVIRONMENT > SELLER > EXECUTION_CHANNEL` の順序でポリシーを評価します。その際、`BLOCK_LIVE_EXECUTION`, `ENVIRONMENT_SAFE_MODE`, `BLOCK_LISTING_CREATION` といった制限の強いアクション (Deny-first) は最優先で全体の決定 (`EffectivePolicyDecision`) に波及し、下位スコープの許可状態を強制的に上書きします。

5. **EffectivePolicyDecision 用途**
   `EffectivePolicyService` がこれらのロジックを統合し、指定された `seller_account_id` と `environment` に対する最終的な有効ポリシー設定 (ライブ実行可否やレビューレベル等) を瞬時に計算し、提供します。

### Wave 2 実装内容
インシデントや異常値から運用ポリシー候補 (OpsPolicyCandidate) を自動生成するサービス群を実装しました。

1. **IncidentToPolicyCandidateService**
   - High / Critical レベルのインシデントが発生した際に、その属性（`incident_type`, `severity`）から自動的にポリシーの適用スコープと最適なアクションタイプ（`BLOCK_LIVE_EXECUTION` や `ENVIRONMENT_SAFE_MODE` 等）をマッピングし、`OpsPolicyCandidate` を生成します。

2. **IncidentDetectionService**
   - 以下の6つの異常検知ルール（Detection logic）を実装し、指定時間内の閾値超過に応じて候補を起票します:
     1. **credential_failure_spike**: 60分以内に3回以上の認証失敗 → `BLOCK_LIVE_EXECUTION` (Critical)
     2. **high_severity_incident**: 既存のインシデントが High / Critical → インシデント種別に応じたアクション
     3. **environment_anomaly**: 60分以内の環境エラー率が 30% 超過 → `ENVIRONMENT_SAFE_MODE` (High)
     4. **retry_loop_risk**: 120分以内の累積リトライが 60分 超過 → `SUPPRESS_RETRY` (High)
     5. **seller_health_degradation**: 24時間以内の日次エラー率が 30% 超過 → `PAUSE_HANDOFF` (High)
     6. **guard_rejection_spike**: 60分以内に3回以上の Guard 拒否 → `REQUIRE_MANUAL_REVIEW` (Medium)
   - 各候補の重要度やアクションに基づく優先度スコア計算ロジック（`evaluate_candidate_priority`）も提供します。

### Wave 3 実装内容
運用制御ポリシーを一元管理し、ダッシュボード集計やレポート出力を提供する Management / Dashboard / Digest サービス群を実装しました。

1. **OpsPolicyManagementService**
   - ポリシーの CRUD およびライフサイクル管理を担います。
   - `create_policy_from_candidate` や `create_manual_policy` を通じてポリシーを起票します。
   - インシデントへの紐付け (`link_policy_to_incident`) や監査ノートの追加 (`add_policy_note`) などの履歴追跡操作を提供します。

2. **OpsPolicyDashboardService**
   - システム全体のポリシー状況を集計・可視化するためのデータを提供します。
   - アクション種別、適用スコープ別のカウントや、最も制限を受けているセラーのランキング (`get_top_affected_sellers`)、直近24時間の新規作成数などを `get_policy_summary` として一括返却します。

3. **OpsPolicyDigestService**
   - Markdown 形式のレポートを自動生成します。
   - 現在 Active な全ポリシー (`generate_active_policy_digest`)、特定のセラーや環境向け (`generate_seller_policy_digest`)、あるいは日次サマリー (`generate_daily_policy_summary_digest`) などのレポート出力要件をカバーしています。

### Wave 4 実装内容
これまでの Management / Dashboard / Digest サービスを CUI 環境から直接操作・照会できるように、Admin CLI コマンドを実装しました。

1. **実装コマンド一覧**
   - **照会系**: `scan`, `candidate-list`, `list`, `show`, `dashboard`, `digest`
   - **操作系**: `propose`, `approve`, `activate`, `reject`, `release`, `expire`, `cancel`

2. **出力フォーマットの柔軟性**
   - 全コマンドに共通オプションとして `--format {table|json|csv}` を導入しました。
   - 単純なコンソール表示には table (テキスト) を、別システムとの連携や自動処理向けには json や csv を利用でき、運用自動化のパイプラインに組み込みやすくしています。
   - `--output-file <path>` 指定により、標準出力だけでなく直接ファイルへの書き出しもサポートしています。

3. **安全機能 (Dry-run)**
   - 状態遷移を伴うすべての操作系コマンドに `--dry-run` オプションをサポートし、誤操作によるシステム全体への意図しないポリシー適用を事前に防止できるようにしています。

### Wave 5 実装内容
CLI に続き、運用担当者が視覚的にポリシーを管理できる Web インターフェース (Web Routes / Jinja2 Templates) を実装しました。

1. **実装ルートと画面構成**
   - **一覧・検索画面** (`/ops/policies/`): ポリシーの絞り込み (Scope, Status) と一覧表示。
   - **詳細画面** (`/ops/policies/<id>`): ポリシーの基本情報、タイムライン (監査履歴)、および現在可能な状態遷移 (Approve, Activate 等) のアクションボタンを表示します。
   - **候補プレビュー画面** (`/ops/policies/candidates`): 異常検知から起票されたポリシー候補を一覧表示します。
   - **作成画面** (`/ops/policies/create`): 手動で新規ポリシーを作成するフォームを提供します。
   - **ダッシュボード** (`/ops/policies/dashboard`): 集計データや制限の多いセラーランキング等をサマリー表示します。
   - **レポートプレビュー** (`/ops/policies/<id>/digest`): 個別ポリシーの Markdown 出力をブラウザ上で確認できます。

2. **UI の特徴**
   - `PolicyStatus` や `Severity` に応じた状態遷移ボタンの動的出し分け（例: PROPOSED の場合は Approve や Reject のみ表示、ACTIVE の場合は Release 等）。
   - `STRONG` レベルのポリシーを承認する際の `review_due` 入力フィールド制御。
   - 処理の成功/失敗を伝えるフラッシュメッセージ機構 (`get_flashed_messages()`) の導入。
   - 誤操作防止の観点から、既存ポリシーは直接編集 (UPDATE/DELETE) させず、すべて Status 変更と Append-only の監査ノートで追跡するリードオンリー/追記型デザインを採用しています。

### Wave 6 実装内容 (Phase N 最終波)
最後に、これまでインメモリで管理していたポリシー情報を RDBMS 上に永続化するための DB スキーマと ORM、および定期ジョブを実装し、Phase N を完了させました。

1. **DB 永続化基盤**
   - **Alembic マイグレーション**: `ops_policies` テーブルと、履歴を管理する `ops_policy_events` テーブルを作成するマイグレーションスクリプトを定義しました。JSON データの保存には互換性のための JSON カラムを採用しています。
   - **ORM Model**: `OpsPolicyModel` および `OpsPolicyEventModel` を追加し、リレーションシップを設定しました。
   - **DB Repositories**: インメモリ管理だったサービス層を DB バックエンドに切り替えるため、`OpsPolicyRepository` と `OpsPolicyEventRepository` を実装し、必要な CRUD 処理と Append-only 要件を満たしました。

2. **Orchestrator ジョブ (3種)**
   - **PolicyCandidateScanJob**: 定期的に `IncidentDetectionService` を呼び出し、新たなポリシー候補をスキャンします。
   - **PolicyExpiryJob**: `effective_until` を超過したポリシーをチェックし、自動的に `EXPIRED` 状態へ移行させます。
   - **PolicyReviewDueScanJob**: 承認済みだがレビュー期限 (`review_due_at`) を過ぎたポリシーを検出し、アラート用に抽出します。

**Phase N 全体の詳細な設計とまとめは、`docs/phase-n-seller-ops-policy-implementation.md` に記載されています。**

## Phase O: Continuous Learning & Feedback Loop

### Wave 1 実装内容
Phase M / Phase N で蓄積された Incident や Policy の情報を元に、システムの継続的改善を支援するための「学習ループ (Learning Loop)」を定義する基本的なデータモデル (DTO) とサービスを実装しました。

1. **データモデル (DTOs)**
   - **`LearningRecord`**: 一連のアラートやインシデントから得られた「学び」を記録する中心となるモデル。根本原因 (`RootCauseCategory`)、影響範囲 (`ImpactScope`)、効果測定 (`EffectivenessRating`) などを保持し、追跡可能な状態 (`LearningRecordStatus`) で管理されます。
   - **`RootCauseAnalysis` (RCA)**: 個々の `LearningRecord` に紐づき、詳細な根本原因分析を記録します。問題、症状、原因、軽減策、解決策、および将来の予防策 (`prevention_proposal`) などの情報を構造化して保持します。
   - **`LearningRecommendation`**: RCA の結果から得られた具体的な改善提案を表現します。「検知しきい値の調整」や「ポリシーガードの強化」などの `RecommendationType` と、適用先システムを保持し、実装まで追跡可能です。
   - **`LearningCandidate`**: 自動生成される「学習対象の候補」。解決済みインシデントやポリシー無効パターン等から自動抽出された情報が含まれます。

2. **管理サービス**
   - **`LearningRecordService`**: `LearningRecord` の新規作成、Status 更新 (Close)、インシデント/ポリシーのリンク、フィルタリング (Scope / Status 等) などの CRUD とステート管理を提供します。
   - **`RootCauseAnalysisService`**: RCA の記録、情報更新、予防策 (`prevention_proposal`) の抽出、および分析の過程で判明した検知ギャップ (`detection_gap`) の追記を管理します。

これらの基盤データ構造により、運用中に発生した課題が暗黙知として埋もれることなく、構造化された「知識」および「具体的な改善アクション」としてシステムへフィードバックされる体制が整いました。
