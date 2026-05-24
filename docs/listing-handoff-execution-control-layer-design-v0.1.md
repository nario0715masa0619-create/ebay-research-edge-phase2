# Phase G 設計書 v0.1
# Listing Handoff / Execution Control Layer

- **Document Path**: `docs/listing-handoff-execution-control-layer-design-v0.1.md`
- **Layer Name**: Phase G / Listing Handoff / Execution Control Layer
- **Repository**: `ebay-research-edge-phase2`
- **Position in Pipeline**:  
  `Collection → Candidate Normalization → Review / Alias / Seed Bridge → Market Evaluation → Profitability Scoring → Ranking / Listing Decision → Listing Handoff / Execution Control → Listing Readiness / Execution → Monitoring / Revise`

---

## 1. 目的

Listing Handoff / Execution Control Layer の目的は、Phase F で生成された `auto_launch_queue` を、既存の Listing Readiness / Execution レイヤへ **安全・監査可能・冪等** に橋渡しすることである。

このレイヤは単に「次へ流す」だけではなく、以下を保証する。

1. **auto_launch と判定された候補だけが実行系へ流れる**
2. **二重投入・重複出品・多重 handoff を防止する**
3. **seller / environment / capacity / cooldown / execution policy を尊重する**
4. **handoff の成否と理由を追跡できる**
5. **失敗・保留・再試行・中断・取消を状態として管理できる**
6. **Phase F の判断と Phase H 以降の実出品処理を、責務分離したまま接続する**

本レイヤは、システム全体を  
**「候補選定システム」から「安全に実行へ渡せる運用システム」へ完成させる制御層**  
である。

---

## 2. 前提

Phase G は以下が実装済みであることを前提とする。

1. **Phase F / Ranking / Listing Decision Layer** が完了している
2. `ListingDecisionResult` または同等の ranking decision が存在する
3. `auto_launch_queue`, `review_queue`, `watch_queue`, `reject_archive` の概念が存在する
4. 既存の **Listing Readiness / Execution** レイヤが利用可能である
5. seller / environment guard、notification、escalation、orchestrator、admin CLI、admin Web が利用可能である
6. persistence, auth, sync/recovery, monitoring/revise が既存基盤として存在する

本レイヤは「何を出品すべきか」を決めるのではなく、  
**「出品してよいと判定されたものを、どう安全に渡すか」** を担う。

---

## 3. 責務

## 3.1 Handoff Eligibility Verification
- Phase F で `auto_launch` と判定された候補について、handoff 直前の最終確認を行う
- stale / blocked / duplicate / already handed off / already listed / policy invalid を確認する
- handoff 可能なものだけを次工程へ渡す

## 3.2 Execution Control
- seller ごとの同時実行数、run ごとの実行上限、cooldown、environment policy を制御する
- handoff 対象を batch 単位・seller 単位で制御する
- readiness / execution 側への投入順を決定する

## 3.3 Idempotent Handoff
- 同一 candidate が複数回連続で execution へ渡されないようにする
- request fingerprint / handoff key / decision linkage により重複投入を抑止する
- 再試行と重複 handoff を区別する

## 3.4 State Management
- handoff の進行状態を状態遷移として保持する
- pending, claimed, dispatched, accepted, rejected, failed, deferred, cancelled などを管理する
- 各遷移に対して actor / reason / timestamp を残す

## 3.5 Failure / Retry / Defer Control
- 一時失敗と恒久失敗を分離する
- retryable error と non-retryable error を分ける
- capacity 超過・rate limit・seller cooldown は defer として扱う
- serious failure は escalation / notification に接続する

## 3.6 Observability / Audit
- handoff 成否を一覧化できるようにする
- どの candidate がいつ誰の run でどこまで進んだか追えるようにする
- execution への handoff 数、失敗数、重複抑止数、defer 数を記録する

---

## 4. 非責務

以下は Phase G の責務外とする。

- Market Evaluation / Profitability / Ranking の再計算
- 実際の listing payload の詳細構築
- eBay API 呼び出しそのものの再実装
- 出品後モニタリングの再実装
- 動的 repricing
- ML / LLM による handoff 最適化
- 外部 WMS / ERP / 会計連携の高度化

---

## 5. 主要概念

## 5.1 Handoff Candidate
Phase F で `auto_launch` と判定され、実行候補になった candidate。

## 5.2 Handoff Request
Execution 系へ渡すための制御単位。candidate / seller / environment / decision / readiness payload reference を含む。

## 5.3 Handoff Attempt
1 回の handoff 実行試行。失敗しても履歴を残す。

## 5.4 Handoff State
handoff request の現在状態。状態遷移管理の中心。

## 5.5 Handoff Batch
同一 run / 同一 seller / 同一 scheduler window などでまとめて実行される handoff 群。

---

## 6. 入力

## 6.1 Ranking / Decision Input
- `ranking_decision_id`
- `candidate_id`
- `seller_account_id`
- `environment`
- `decision_class`
- `ranking_score`
- `queue_type`
- `queue_rank`
- `execution_blocked`
- `block_reasons`
- `recheck_required`
- `stale_flag`
- `decision_reason`
- `explanation_lines`

## 6.2 Candidate / Listing Context Input
- `canonical_title`
- `brand`
- `model`
- `mpn`
- `gtin`
- `condition_family`
- `variation_signature`
- `bundle_signature`
- `source_refs`
- `market_evaluation_id`
- `profitability_score_id`

## 6.3 Execution Policy Input
- `seller_execution_policy`
- `environment_policy`
- `max_handoff_per_run`
- `max_handoff_per_seller`
- `seller_cooldown_seconds`
- `duplicate_suppression_window_seconds`
- `retry_policy`
- `defer_policy`
- `escalation_policy`
- `readiness_policy`

## 6.4 Existing Runtime Context
- `existing_listing_state`
- `existing_handoff_state`
- `recent_handoff_attempts`
- `recent_execution_failures`
- `seller_active_execution_count`
- `current_scheduler_run_id`
- `current_batch_id`

## 6.5 任意入力
- `inventory_lock_hint`
- `listing_slot_availability`
- `manual_override_flags`
- `operator_hold_flag`
- `seller_daily_limit`
- `execution_channel`

---

## 7. 出力

## 7.1 主出力
- `handoff_id`
- `candidate_id`
- `ranking_decision_id`
- `seller_account_id`
- `environment`
- `handoff_status`
- `handoff_decision`
- `execution_allowed`
- `dispatch_target`
- `dispatch_priority`
- `batch_id`
- `scheduler_run_id`
- `idempotency_key`
- `duplicate_suppressed`
- `deferred`
- `retryable`
- `block_reasons`
- `failure_reason`
- `next_retry_at`
- `handoff_payload_ref`
- `explanation_lines`
- `created_at`
- `updated_at`

## 7.2 handoff_decision
- `dispatch_now`
- `defer`
- `reject_handoff`
- `cancel`
- `retry_later`

## 7.3 handoff_status
- `pending`
- `claimed`
- `validated`
- `dispatched`
- `accepted`
- `rejected`
- `failed`
- `deferred`
- `cancelled`
- `completed`

## 7.4 補助出力
- `attempt_count`
- `last_attempt_at`
- `last_error_code`
- `last_error_summary`
- `audit_lines`
- `policy_snapshot`
- `state_transition_summary`

---

## 8. 状態遷移

## 8.1 基本状態
- `pending`
- `claimed`
- `validated`
- `dispatched`
- `accepted`
- `rejected`
- `failed`
- `deferred`
- `cancelled`
- `completed`

## 8.2 代表的な遷移

### 正常系
1. `pending`
2. `claimed`
3. `validated`
4. `dispatched`
5. `accepted`
6. `completed`

### validation 失敗
1. `pending`
2. `claimed`
3. `rejected`

### execution 一時失敗
1. `pending`
2. `claimed`
3. `validated`
4. `dispatched`
5. `failed`
6. `deferred`
7. `pending`（再試行対象に戻す場合）

### capacity / cooldown による保留
1. `pending`
2. `claimed`
3. `deferred`

### 手動停止 / policy block
1. `pending`
2. `claimed`
3. `cancelled`

## 8.3 状態遷移ルール
- `dispatched` の前に `validated` が必須
- `accepted` は execution 側が handoff を受理した時のみ遷移
- `completed` は readiness / execution への handoff が成功し、重複再投入不要と判定された時に遷移
- `rejected` は policy / duplicate / invalid / stale などの handoff 不可で確定した場合
- `failed` は実行試行が行われたが失敗した場合
- `deferred` は retryable かつ今は流せない場合
- `cancelled` は operator / policy / system override による取消

---

## 9. 安全制御

## 9.1 Hard Gate
以下のいずれかに該当する場合、handoff を禁止する。

- `decision_class != auto_launch`
- `execution_blocked == true`
- `recheck_required == true`
- `stale_flag == true`
- ranking / profitability / market の重要入力欠損
- seller / environment policy 違反
- blacklist / restricted / prohibited category
- duplicate suppression window 内の同一 candidate
- 既に active listing か、同一 candidate が listing 中
- operator hold / manual block
- invalid readiness payload

## 9.2 Capacity Control
- run 単位の handoff 上限を超えた場合は `defer`
- seller 単位の handoff 上限を超えた場合は `defer`
- seller active execution count が上限に達している場合は `defer`
- cooldown 中の seller は `defer`

## 9.3 Duplicate Suppression
- `idempotency_key` で同一 handoff を識別する
- 直近 window 内の同一 candidate / seller / environment の重複投入を禁止する
- ranking decision が同じでも execution handoff は一度だけ通す
- retry は新しい handoff ではなく attempt として扱う

## 9.4 Retry Safety
- retryable error のみ再試行可
- retry 回数上限を持つ
- exponential backoff または fixed defer を設定可
- repeated failure は escalation に接続する
- non-retryable error は `rejected` または `cancelled`

## 9.5 Environment Safety
- production / sandbox / dev を混同しない
- seller binding と environment binding を必ず確認する
- 実 execution channel を誤 environment へ向けない

---

## 10. 判定基準

## 10.1 dispatch_now
以下をすべて満たす場合:
- `decision_class == auto_launch`
- stale でない
- blocked でない
- duplicate でない
- capacity 内
- cooldown 外
- readiness payload が妥当
- execution policy が許可

## 10.2 defer
以下のいずれか:
- capacity full
- seller cooldown active
- temporary execution saturation
- retry window 未到来
- scheduled defer policy

## 10.3 reject_handoff
以下のいずれか:
- ranking decision が auto_launch でない
- stale / recheck_required
- duplicate suppression hit
- invalid candidate linkage
- invalid readiness payload
- restricted / prohibited / blocked by policy
- already listed or already handed off

## 10.4 retry_later
以下のいずれか:
- downstream temporary failure
- transient transport error
- rate limit / temporary external block
- short-lived dependency unavailable

## 10.5 cancel
以下のいずれか:
- operator cancel
- seller policy changed
- environment changed
- manual override stop
- queue invalidated by newer decision

---

## 11. ドメインモデル案

## 11.1 `HandoffInput`
Phase F の ranking decision と execution 制御情報をまとめた DTO。

## 11.2 `HandoffValidationResult`
validation と hard gate 結果を保持するモデル。
- `is_valid`
- `is_duplicate`
- `is_stale`
- `is_blocked`
- `should_defer`
- `block_reasons`
- `defer_reasons`

## 11.3 `HandoffAttempt`
1 回の handoff 試行を表現するモデル。
- `attempt_id`
- `handoff_id`
- `attempt_number`
- `attempt_status`
- `error_code`
- `error_summary`
- `started_at`
- `finished_at`

## 11.4 `HandoffResult`
最終的な handoff 結果。
- `handoff_id`
- `handoff_status`
- `handoff_decision`
- `execution_allowed`
- `retryable`
- `deferred`
- `next_retry_at`
- `explanation_lines`

## 11.5 `HandoffTransition`
状態遷移履歴。
- `from_status`
- `to_status`
- `transition_reason`
- `actor`
- `occurred_at`

---

## 12. 推奨実装コンポーネント

- `src/handoff/models.py`
- `src/handoff/config.py`
- `src/handoff/eligibility_validator.py`
- `src/handoff/duplicate_guard.py`
- `src/handoff/capacity_controller.py`
- `src/handoff/cooldown_policy.py`
- `src/handoff/retry_policy.py`
- `src/handoff/state_machine.py`
- `src/handoff/handoff_service.py`
- `src/handoff/result_mapper.py`
- `src/handoff/bootstrap.py`
- `src/repositories/persistent_handoff_repository.py`

必要に応じて:
- `persistent_handoff_attempt_repository.py`
- `persistent_handoff_transition_repository.py`
- DB models
- Alembic migration
- CLI / Web / Orchestrator integration

---

## 13. 永続化

## 13.1 推奨テーブル
- `listing_handoffs`
- `listing_handoff_attempts`
- `listing_handoff_transitions`
- `listing_handoff_audits`（任意）

## 13.2 保存すべき内容
- handoff 最新状態
- decision linkage
- seller / environment / batch / scheduler linkage
- idempotency key
- duplicate suppression result
- defer / retry / failure 情報
- block reasons
- explanation lines
- attempt history
- state transition history
- created / updated timestamps

---

## 14. Orchestrator 統合

## 14.1 新規ジョブ
- `listing_handoff_control_job`

## 14.2 入力対象
- 最新 `listing_decisions` のうち `decision_class = auto_launch`
- `queue_type = auto_launch_queue`
- seller / environment / candidate で絞り込み可能

## 14.3 処理フロー
1. auto launch queue 取得
2. duplicate / stale / block / capacity / cooldown 検証
3. handoff candidate claim
4. readiness payload reference 解決
5. execution handoff 実行
6. state 更新
7. retry / defer / reject / completed 反映
8. notification / escalation 連携
9. metrics / job run 更新

## 14.4 サポート
- `dry_run`
- `limit`
- `seller_account_id`
- `environment`
- `candidate_id`
- `batch_id`
- `force_retry`
- `force_defer`

---

## 15. CLI / Web で最低限見えるべきもの

## 15.1 CLI
- `ops handoff run`
- `ops handoff show`
- `ops handoff recent`
- `ops handoff pending`
- `ops handoff deferred`
- `ops handoff failed`
- `ops handoff retry`
- `ops handoff cancel`

## 15.2 Web
- handoff list
- handoff detail
- pending / deferred / failed queue view
- attempt history
- transition timeline

## 15.3 表示項目
- candidate summary
- ranking decision summary
- handoff status
- handoff decision
- execution allowed / blocked
- duplicate suppressed
- defer reasons
- failure reasons
- next retry time
- transition timeline
- attempt history

---

## 16. 例外処理

## 16.1 入力欠損
- ranking decision 不在
- candidate 不在
- profitability / market linkage 不在
- readiness payload reference 不在
→ `reject_handoff` または `manual_review` へ戻す

## 16.2 stale data
- ranking / profitability / market が stale
→ `deferred` または `reject_handoff`
→ `recheck_required` を通知可能

## 16.3 duplicate / already listed
- 同一 candidate が既に handoff 済み
- 既に listing 中
→ `reject_handoff`
→ duplicate suppression として監査に残す

## 16.4 temporary downstream error
- readiness unavailable
- execution temporary unavailable
- rate limit
→ `failed` → `deferred` → retry_later

## 16.5 policy change after ranking
- seller policy changed
- environment switched
- category blocked
→ `cancelled` または `reject_handoff`

---

## 17. 監査・説明責任

- どの decision から handoff が生まれたか追えること
- なぜ handoff されたか / されなかったか説明できること
- duplicate suppression の理由が残ること
- defer / retry / cancel の理由が残ること
- secret や credential を保存しないこと
- actor / scheduler / batch 情報を最小限監査可能に残すこと

---

## 18. 受け入れ条件

以下をすべて満たした時、Phase G v0.1 を受け入れ可能とする。

## 18.1 機能受け入れ条件
- `auto_launch_queue` を入力に handoff 結果を生成できる
- `dispatch_now / defer / reject_handoff / retry_later / cancel` を返せる
- `handoff_status`, `block_reasons`, `failure_reason`, `next_retry_at` を返せる
- readiness / execution への hand-off 導線がある
- duplicate suppression が動作する

## 18.2 品質受け入れ条件
- stale / blocked / duplicate / already listed を誤って dispatch しない
- idempotent に再実行できる
- retryable と non-retryable を区別できる
- seller / environment guard を壊さない
- pytest が全件 PASS する

## 18.3 運用受け入れ条件
- queue 消費状況を CLI / Web で確認できる
- failed / deferred handoff を追跡できる
- repeated failure を escalation へ接続できる
- auto launch 実行が seller 容量を超えて暴走しない

---

## 19. 完了条件

- Listing Handoff / Execution Control Layer が end-to-end で動作する
- `auto_launch_queue` から安全に readiness / execution へ hand-off できる
- duplicate suppression, capacity control, cooldown, retry, defer, cancel が機能する
- repository / migration / orchestrator / CLI / Web が統合される
- 全テスト PASS
- commit / push 完了

---

## 20. 推奨コミットメッセージ

`Add Phase G listing handoff and execution control layer with idempotent dispatch and safety gating`

---

## 21. 要約

Phase G は、Phase F で作られた `auto_launch_queue` を、  
**安全に、重複なく、容量制御付きで実 execution 系へ渡すための制御層** である。

このレイヤでは、
- gate validation
- duplicate suppression
- stale / block / cooldown / capacity 制御
- retry / defer / cancel
- state transition / audit

を担い、候補を  
**「出せる」から「安全に出し始められる」**  
へ変換する。

これによりプロジェクト全体は、  
**利益候補を見つけて並べるシステム** から、  
**爆益候補を安全な実行パイプラインへ流し込む運用システム**  
へ進化する。
