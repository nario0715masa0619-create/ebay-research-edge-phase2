# Phase F 設計書 v0.1
# Ranking / Listing Decision Layer

- **Document Path**: `docs/ranking-listing-decision-layer-design-v0.1.md`
- **Layer Name**: Phase F / Ranking / Listing Decision Layer
- **Repository**: `ebay-research-edge-phase2`
- **Position in Pipeline**:  
  `Collection → Candidate Normalization → Review / Alias / Seed Bridge → Market Evaluation → Profitability Scoring → Ranking / Listing Decision → Listing Readiness / Execution`

---

## 1. 目的

Ranking / Listing Decision Layer の目的は、Phase D の Market Evaluation と Phase E の Profitability Scoring の結果を統合し、候補商品を **運用上の優先順位** に変換することである。  
このレイヤは、単に「利益が高い」候補を並べるだけではなく、以下を同時に満たす判断を行う。

1. **今すぐ出すべき候補を上位に押し上げる**
2. **レビューが必要な候補を、危険度と期待値の両面から整列する**
3. **watch / reject を明確に分け、人的リソースを浪費しない**
4. **seller / environment / policy ごとの運用制約を尊重する**
5. **Listing Readiness / Execution に安全に橋渡しする**

本レイヤは、プロジェクト全体のゴールである  
**「爆益候補を、優先順位付きの実行可能キューへ変換する」**  
ための最終意思決定レイヤである。

---

## 2. 前提

Phase F は以下が実装済みであることを前提とする。

1. **CanonicalProductCandidate** が存在する
2. **Review / Alias / Seed Bridge** により candidate の同一性・曖昧性が整理されている
3. **MarketEvaluationResult** が存在する
4. **ProfitabilityScoreResult** または同等の利益評価結果が存在する
5. seller / environment / notification / escalation / admin CLI / admin Web / orchestrator が既存基盤として利用可能である
6. Listing Readiness / Execution がすでに存在し、Phase F はその直前の判断レイヤとして機能する

本レイヤは「市場成立性」や「利益計算」を再実装するものではない。  
それらの結果を入力として、**運用上どの順で、どの安全度で、どの方法で扱うか** を決定するレイヤである。

---

## 3. 責務

Phase F の責務は以下のとおり。

### 3.1 優先順位付け
- すべての候補に対して `ranking_score` を付与する
- seller 単位 / marketplace 単位 / environment 単位で優先度を出せるようにする
- 利益だけでなく、安全性・確信度・運用状態を反映する

### 3.2 Listing Decision
各候補を最低限以下に分類する。
- `auto_launch`
- `manual_review`
- `watchlist`
- `reject`

必要に応じて補助ステータスを持ってよい。
- `ready_but_deferred`
- `blocked_by_policy`
- `blocked_by_capacity`
- `stale_recheck_required`

### 3.3 実行キュー生成
- auto_launch 候補から Listing Readiness / Execution に渡す対象を作る
- manual_review 候補から review queue を作る
- watchlist 候補を再評価対象として残す
- reject 候補は理由付きで保存する

### 3.4 安全ガード
- 重大な unsafe reason がある候補を自動出品へ流さない
- review_required が true の候補を auto_launch へ流さない
- seller / environment guard を尊重する
- 設定上の最大同時投入件数や seller 容量制約を尊重する

### 3.5 説明可能性
- なぜ上位なのか
- なぜ auto_launch / manual_review / watchlist / reject なのか
を `decision_reason` と `explanation_lines` で追えるようにする

---

## 4. 非責務

以下は Phase F の責務外とする。

- Profitability Score の再計算
- Market Evaluation の再取得
- 画像判定や ML による最終判断
- 実際の出品処理そのもの
- 動的 repricing
- 広告 / 在庫保管 / 税務の高度最適化
- 外部チケットシステムとの高度連携

---

## 5. 入力

Phase F は最低限以下を入力として受け取る。

### 5.1 Candidate Input
- `candidate_id`
- `seller_account_id`
- `environment`
- `canonical_title`
- `brand`
- `model`
- `mpn`
- `gtin`
- `condition_family`
- `variation_signature`
- `bundle_signature`
- `review_required`
- `ambiguity_flags`
- `candidate_status`

### 5.2 Market Evaluation Input
- `market_evaluation_id`
- `evaluation_status`
- `comparable_count`
- `price_low`
- `price_avg_or_median`
- `price_high`
- `market_confidence`
- `competition_proxy`
- `demand_proxy`
- `unsafe_reasons`
- `category_alignment_score`
- `condition_alignment_score`
- `attribute_alignment_score`

### 5.3 Profitability Input
- `profitability_score_id`
- `scoring_status`
- `expected_net_profit`
- `expected_margin`
- `expected_roi`
- `confidence_adjusted_profit`
- `profitability_score`
- `decision_status`（Phase E の暫定判断）
- `decision_reason`
- `unsafe_reasons`
- `explanation_lines`

### 5.4 Operational Input
- `seller_policy`
- `environment_policy`
- `listing_capacity_policy`
- `manual_review_policy`
- `auto_launch_policy`
- `max_auto_launch_per_run`
- `max_auto_launch_per_seller`
- `cooldown_policy`
- `staleness_policy`
- `blacklist / block rules`
- `existing_listing_state`（必要に応じて）

### 5.5 任意入力
- `inventory_available_hint`
- `seller_daily_limit`
- `review_queue_backlog`
- `last_ranked_at`
- `last_decision_at`
- `recent_decision_count_by_seller`
- `seasonality_hint`

---

## 6. 出力

### 6.1 主出力
- `ranking_decision_id`
- `candidate_id`
- `seller_account_id`
- `environment`
- `ranking_score`
- `decision_class`
- `decision_reason`
- `decision_confidence`
- `launch_priority_bucket`
- `review_priority_bucket`
- `execution_blocked`
- `block_reasons`
- `queue_type`
- `queue_rank`
- `ready_for_listing`
- `recheck_required`
- `stale_flag`
- `explanation_lines`
- `created_at`
- `updated_at`

### 6.2 decision_class
- `auto_launch`
- `manual_review`
- `watchlist`
- `reject`

### 6.3 queue_type
- `auto_launch_queue`
- `review_queue`
- `watch_queue`
- `reject_archive`

### 6.4 補助出力
- `ranking_components`
- `policy_snapshot`
- `unsafe_reasons`
- `fallback_flags`
- `source_refs`
- `next_action_hint`

---

## 7. 判定基準

Phase F の判定は、単一スコアではなく複数のゲートと優先度計算の組み合わせで行う。

### 7.1 Gate 1: Reject Gate
以下のいずれかを満たす場合は `reject` とする。
- `profitability_score <= 0` または極端に低い
- `confidence_adjusted_profit <= 0`
- `expected_net_profit <= 0`
- `market_confidence < reject threshold`
- Phase D / E の重大 `unsafe_reasons` が存在する
- `scoring_status in (invalid_input, input_incomplete)`
- `evaluation_status` が致命的失敗
- seller / environment policy 上で出品不可
- blocklist / prohibited / restricted category

### 7.2 Gate 2: Auto Launch Eligibility Gate
以下をすべて満たす場合のみ `auto_launch` 候補とする。
- `review_required == false`
- `profitability decision` が launch 相当
- `confidence_adjusted_profit >= auto_launch_min_profit`
- `expected_margin >= auto_launch_min_margin`
- `expected_roi >= auto_launch_min_roi`
- `market_confidence >= auto_launch_min_market_confidence`
- 重大 `unsafe_reasons` がない
- `execution_blocked == false`
- seller の同時出品上限 / rate limit / policy を超えない
- stale ではない、または stale でも再評価済み

### 7.3 Gate 3: Manual Review Gate
以下のいずれかで `manual_review` とする。
- 利益は十分あるが `review_required == true`
- ambiguity / variation / bundle の確認が必要
- market / profitability の confidence が中間帯
- fallback で重要でない設定を補った
- suspicious outlier
- auto_launch 条件には届かないが watch に落とすには惜しい
- seller 固有ポリシーで人手確認必須

### 7.4 Gate 4: Watch Gate
以下のいずれかで `watchlist` とする。
- 利益はわずかに正だが launch には弱い
- demand はあるが margin が薄い
- seasonality / timing 待ち
- stale 再評価待ち
- seller capacity の都合で defer が必要
- auto_launch 候補だが今 run では枠外

---

## 8. Ranking Score

`ranking_score` は `0〜100` を想定し、Phase E の利益性と Phase D の市場性、Phase F の運用性を統合して計算する。

### 8.1 基本成分
- `profitability_component`
- `margin_component`
- `roi_component`
- `market_confidence_component`
- `demand_component`
- `competition_component`
- `review_penalty_component`
- `unsafe_penalty_component`
- `staleness_penalty_component`
- `capacity_penalty_component`

### 8.2 推奨合成式（v0.1）
`ranking_score = (normalized_confidence_adjusted_profit * 0.35 + normalized_profitability_score * 0.20 + normalized_market_confidence * 0.10 + normalized_margin * 0.10 + normalized_roi * 0.10 + normalized_demand_proxy * 0.10 - normalized_review_penalty * 0.10 - normalized_unsafe_penalty * 0.10 - normalized_staleness_penalty * 0.05 - normalized_capacity_penalty * 0.05) * 100`

### 8.3 補正ルール
- `auto_launch` 候補は seller ごとに `queue_rank` を付与する
- `manual_review` は「利益期待値 × 危険度」で優先順位を付ける
- `watchlist` は「将来性 × 再評価必要度」で順位付けする
- `reject` は順位より理由の保存を重視する

---

## 9. Decision Buckets

### 9.1 launch_priority_bucket
- `urgent`
- `high`
- `normal`
- `deferred`

### 9.2 review_priority_bucket
- `critical_review`
- `high_review`
- `normal_review`
- `low_review`

### 9.3 付与ルール例
- `urgent`: 高利益・高 confidence・競争低・即時投入可能
- `critical_review`: 利益が高いが unsafe / ambiguity が強い
- `deferred`: 利益は良いが seller capacity / cooldown / timing で保留
- `low_review`: 利益も危険度も中途半端

---

## 10. 実行制御

### 10.1 Auto Launch Queue 制御
- `max_auto_launch_per_run`
- `max_auto_launch_per_seller`
- `seller_cooldown_seconds`
- `environment guard`
- `capacity exhaustion`
- `duplicate suppression`

### 10.2 Review Queue 制御
- `high expected profit` を上位へ
- 同じ seller で backlog が偏りすぎないよう調整可
- 同一系統候補の重複レビューを抑制可

### 10.3 Watch Queue 制御
- stale 期間を超えたら再評価対象へ戻す
- 価格改善や source cost 改善があれば再昇格可能

---

## 11. Open Questions

### 11.1 Ranking Scope
- ランキングは **全 seller 横断** か、**seller ごと** を基本とするか  
**暫定案**: v0.1 は `seller_account_id` 単位を主とし、全体ランキングは補助ビューとする

### 11.2 Capacity Policy
- `max_auto_launch_per_run` と `max_auto_launch_per_seller` を config 固定にするか、seller policy テーブルで持つか  
**暫定案**: v0.1 は config default + seller override

### 11.3 Staleness Threshold
- market / profitability の結果が何時間で stale 扱いか  
**暫定案**: v0.1 は `MARKET_EVAL_STALE_HOURS` と `PROFITABILITY_STALE_HOURS` を別設定にする

### 11.4 Watchlist Promotion
- watch 候補を何をきっかけに再昇格させるか  
**暫定案**: source cost 変化、market re-eval、manual reopen、scheduled refresh

### 11.5 Review Priority Strategy
- review queue は「利益最大化」優先か「危険解消」優先か  
**暫定案**: v0.1 は `expected upside × risk severity` の合成優先度を採用

### 11.6 Duplicate Decision Handling
- 同一 candidate に対する連続 decision を毎回新規保存するか、latest を upsert するか  
**暫定案**: latest は upsert、主要変化は transition / audit に残す

### 11.7 Listing Readiness Hand-off
- auto_launch は即 readiness queue に流すか、Phase F の中でバッファを持つか  
**暫定案**: v0.1 は readiness queue に hand-off し、Phase F 自体は判断に専念する

---

## 12. ドメインモデル案

### 12.1 `RankingInput`
- candidate / market / profitability / policy / seller capacity を統合した入力 DTO

### 12.2 `RankingComponents`
- `profit_component`
- `market_component`
- `risk_component`
- `review_penalty`
- `capacity_penalty`
- `staleness_penalty`
- `queue_adjustment`

### 12.3 `ListingDecisionResult`
- `ranking_decision_id`
- `ranking_score`
- `decision_class`
- `decision_reason`
- `queue_type`
- `queue_rank`
- `execution_blocked`
- `block_reasons`
- `next_action_hint`
- `explanation_lines`

### 12.4 `DecisionTransition`
- decision の変更履歴保存用モデル（任意）

---

## 13. 推奨実装コンポーネント

- `src/ranking/models.py`
- `src/ranking/config.py`
- `src/ranking/ranking_components.py`
- `src/ranking/eligibility_gate.py`
- `src/ranking/decision_engine.py`
- `src/ranking/queue_allocator.py`
- `src/ranking/staleness_policy.py`
- `src/ranking/scoring_service.py`
- `src/ranking/result_mapper.py`
- `src/ranking/bootstrap.py`
- `src/repositories/persistent_ranking_decision_repository.py`

必要に応じて:
- DB models
- Alembic migration
- Admin CLI
- Admin Web
- Orchestrator job

---

## 14. Orchestrator 統合

### 14.1 新規ジョブ
- `ranking_listing_decision_job`

### 14.2 入力対象
- 最新の `profitability_scores`
- 必要に応じて最新 `market_evaluation_results`
- seller / environment / candidate 単位で絞り込み可能

### 14.3 出力
- auto launch queue
- manual review queue
- watch queue
- reject archive

### 14.4 サポート
- `dry_run`
- `limit`
- `seller_account_id`
- `environment`
- `candidate_id`
- `queue_type_filter`

---

## 15. CLI / Web で最低限見えるべきもの

### 15.1 CLI
- `ops ranking run`
- `ops ranking show`
- `ops ranking recent`
- `ops ranking auto-launch`
- `ops ranking review`
- `ops ranking watch`
- `ops ranking reject`

### 15.2 Web
- ranking list
- decision detail
- auto launch queue view
- review queue view
- watchlist view
- blocked / rejected view

### 15.3 表示項目
- candidate summary
- profitability summary
- market summary
- ranking score
- decision class
- queue rank
- block reasons
- explanation lines

---

## 16. 例外処理

### 16.1 重要入力欠損
- profitability result 不在
- market evaluation 不在
- candidate 不在
- seller policy 取得不可（重大）
→ `decision_class = manual_review` または `reject`

### 16.2 stale data
- market / profitability が stale
→ `recheck_required = true`
→ auto_launch 禁止

### 16.3 policy contradiction
- 利益は高いが seller policy で禁止
→ `execution_blocked = true`
→ `manual_review` または `reject`

### 16.4 capacity overflow
- auto_launch 候補は十分あるが容量不足
→ `ready_but_deferred`
→ watchlist ではなく deferred bucket へ

---

## 17. 受け入れ条件

以下をすべて満たした時、Phase F v0.1 を受け入れ可能とする。

### 17.1 機能受け入れ条件
- profitability と market の結果を入力に ranking / decision を出せる
- `auto_launch / manual_review / watchlist / reject` を返せる
- queue_type と queue_rank を返せる
- block reasons / explanation lines を返せる
- Listing Readiness へ hand-off 可能な output を作れる

### 17.2 品質受け入れ条件
- deterministic な出力である
- seller / environment guard を壊さない
- important missing input を silent success しない
- stale / blocked / capacity overflow を誤って auto_launch にしない
- pytest が全件 PASS する

### 17.3 運用受け入れ条件
- high-profit candidates が review queue と auto-launch queue で適切に上位化される
- review_required 候補が誤って自動出品されない
- reject 理由が追跡可能
- defer / watch / reject の境界が説明可能

---

## 18. 完了条件

- Ranking / Listing Decision Layer が end-to-end で動作する
- auto launch / review / watch / reject の分類が安定する
- queue 生成が行える
- Listing Readiness への hand-off が可能
- repository / migration / orchestrator / CLI / Web が統合される
- 全テスト PASS
- commit / push 完了

---

## 19. 推奨コミットメッセージ

`Add Phase F ranking and listing decision layer with queue allocation and launch gating`

---

## 20. 要約

Phase F は、Phase D の市場評価と Phase E の利益評価を、  
**実行優先順位と出品判断** に変換するレイヤである。

このレイヤでは、
- 利益の厚さ
- 市場の確信度
- unsafe / review 要因
- seller / environment 制約
- stale / capacity / cooldown

を統合して、候補を  
`auto_launch / manual_review / watchlist / reject`  
へ機械的に分類する。

これによりプロジェクト全体は、  
**儲かりそうな候補を見つけるシステム** から、  
**爆益候補を安全に実行キューへ流し込むシステム**  
へ進化する。
