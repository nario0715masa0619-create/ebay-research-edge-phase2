# Profitability Scoring Layer 設計書 v0.1

- Document Path: `docs/profitability-scoring-layer-design-v0.1.md`
- Layer Name: Phase E / Profitability Scoring Layer
- Repository: `ebay-research-edge-phase2`
- Position in Pipeline:  
  `Collection → Candidate Normalization → Review / Alias / Seed Bridge → Market Evaluation → Profitability Scoring → Opportunity Ranking / Listing Decision`

## 1. 目的

Profitability Scoring Layer の目的は、Phase D の Market Evaluation までで得られた「市場成立性」を、実際に利益が出るかどうかという観点に変換し、候補商品を `launch_now / review_required / watch / reject` に分類できるようにすることである。

このレイヤは、単に「売れているか」ではなく、以下を総合的に判定する。

1. 期待売価で利益が残るか
2. 送料・手数料・返品・破損・誤判定リスクを含めても成立するか
3. confidence を掛けたあとでも十分な利益密度があるか
4. 自動出品候補にすべきか、人間レビューに回すべきか
5. 同じように見える候補の中で、どれを優先すべきか

本レイヤは、プロジェクト全体の北極星である  
「爆益候補を継続的に上位へ押し上げる」  
ための、利益判定の中核レイヤである。

## 2. ゴール

### 2.1 機能ゴール
- 候補商品ごとに、説明可能な利益スコアを算出する
- 期待純利益・利益率・ROI・confidence-adjusted profit を返す
- 不確実性やリスクを penalty として反映する
- 自動出品候補 / 要レビュー / 様子見 / 却下 を分類する
- CLI / Web / Orchestrator から一貫して実行・閲覧できる

### 2.2 ビジネスゴール
- 単なる候補数ではなく、利益密度の高い候補を優先する
- 誤出品や薄利出品を減らす
- 人間の確認対象を、本当にグレーな案件へ絞る
- 半自動運用でも利益の厚い商品を先に処理できるようにする

## 3. スコープ

### 3.1 In Scope
- 利益計算用ドメインモデル
- 入力契約の固定
- 費用構造の推定
- リスク penalty の適用
- confidence 調整後利益の算出
- `launch_now / review_required / watch / reject` の判定
- ranking score の算出
- evidence / explanation の生成
- 永続化
- Orchestrator / CLI / Web 統合

### 3.2 Out of Scope
- 実際の eBay 出品価格最適化の継続的チューニング
- 動的 repricing
- ML / LLM による利益予測
- 実売後の実績学習ループ
- 需要予測モデルの高度化
- 広告費・在庫保管費・税務計算の完全自動化
- 為替予約やリアルタイム輸送費APIの高度統合

## 4. 前提依存

Profitability Scoring は以下の前段レイヤに依存する。

1. `CanonicalProductCandidate`
2. Review / Alias / Seed Bridge
3. `MarketEvaluationResult`
4. `MarketEvaluationEvidence`
5. Source cost / shipping / seller context / environment guard

このため、本レイヤは Phase D 以前の結果を再利用するレイヤであり、商品同一性や市場妥当性を再判定するのではなく、それらを入力として利益を計算する。

## 5. 入力

### 5.1 必須入力

#### Candidate / Identity
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

#### Source Cost
- `source_price`
- `source_shipping_cost`
- `source_additional_cost`
- `source_currency`
- `source_platform`
- `source_item_url`
- `source_condition_note`

#### Market Evaluation
- `market_evaluation_id`
- `evaluation_status`
- `comparable_count`
- `price_low`
- `price_avg_or_median`
- `price_high`
- `category_alignment_score`
- `condition_alignment_score`
- `attribute_alignment_score`
- `competition_proxy`
- `demand_proxy`
- `market_confidence`
- `unsafe_reasons`

#### Operational / Policy Inputs
- `seller_fee_profile`
- `payment_cost_policy`
- `shipping_policy`
- `risk_policy`
- `currency_conversion_rate`（必要時）
- `manual_review_policy`

### 5.2 任意入力
- `historical_sell_through_hint`
- `marketplace_region`
- `target_listing_format`
- `packaging_cost_estimate`
- `handling_cost_estimate`
- `return_rate_hint`
- `damage_rate_hint`
- `special_restriction_flags`

## 6. 出力

Profitability Scoring Layer は最低限以下を返す。

- `profitability_score_id`
- `candidate_id`
- `market_evaluation_id`
- `scoring_status`
- `expected_sale_price_low`
- `expected_sale_price_base`
- `expected_sale_price_high`
- `effective_source_cost`
- `estimated_marketplace_fee`
- `estimated_payment_cost`
- `estimated_outbound_shipping`
- `estimated_packaging_cost`
- `estimated_handling_cost`
- `risk_penalty_total`
- `competition_penalty`
- `ambiguity_penalty`
- `expected_net_profit`
- `expected_margin`
- `expected_roi`
- `confidence_multiplier`
- `confidence_adjusted_profit`
- `profitability_score`
- `decision_status`
- `decision_reason`
- `review_required`
- `unsafe_reasons`
- `explanation_lines`
- `created_at`
- `updated_at`

## 7. 中核設計思想

1. Raw Profit ではなく Confidence-Adjusted Profit を重視する  
   見かけ上の利益が高くても、不確実性が高ければスコアを下げる。

2. 説明可能性を最優先する  
   なぜ `launch_now / review_required / watch / reject` になったのかを `explanation_lines` で追えること。

3. 安全側に倒す  
   入力欠損や市場不確実性があるときは、自動 Launch ではなく Review または Reject に寄せる。

4. 固定費よりも総コストを重視する  
   仕入れ価格だけでなく、送料・決済・破損・返品・曖昧性のペナルティまで含める。

5. 実装初期はシンプルでよい  
   v0.1 では説明可能な deterministic scoring を優先し、後から係数改善可能な構造にする。

## 8. ドメインモデル

### 8.1 `ProfitabilityInput`
利益計算に必要な入力をまとめる DTO。

主フィールド:
- `candidate_id`
- `market_evaluation_id`
- `source_price`
- `source_shipping_cost`
- `source_additional_cost`
- `expected_sale_price_low`
- `expected_sale_price_base`
- `expected_sale_price_high`
- `market_confidence`
- `comparable_count`
- `competition_proxy`
- `demand_proxy`
- `review_required`
- `ambiguity_flags`
- `unsafe_reasons`
- `seller_fee_profile`
- `shipping_policy`
- `risk_policy`

### 8.2 `ProfitabilityComponentBreakdown`
利益式の各成分を保持する。

- `effective_source_cost`
- `marketplace_fee`
- `payment_cost`
- `outbound_shipping`
- `packaging_cost`
- `handling_cost`
- `risk_penalty_total`
- `competition_penalty`
- `ambiguity_penalty`
- `other_penalty_total`

### 8.3 `ProfitabilityResult`
最終スコア結果。

- `profitability_score_id`
- `expected_net_profit`
- `expected_margin`
- `expected_roi`
- `confidence_multiplier`
- `confidence_adjusted_profit`
- `profitability_score`
- `decision_status`
- `decision_reason`
- `review_required`
- `unsafe_reasons`
- `explanation_lines`

## 9. 価格基準の決め方

### 9.1 Expected Sale Price
Phase D の market evaluation から得られた価格帯を、利益計算用の期待売価へ変換する。

基本ルール:
- `expected_sale_price_low = price_low`
- `expected_sale_price_high = price_high`
- `expected_sale_price_base = price_avg_or_median`

補正ルール:
- `comparable_count` が少ない場合は base price の信頼度を下げる
- `category_alignment_score` / `condition_alignment_score` / `attribute_alignment_score` が低い場合は base price を保守的に下方補正してよい
- ambiguity が高い場合は `price_low` 側へ寄せた conservative base を使ってよい

推奨 v0.1 ルール:
- `market_confidence >= 0.85` の場合: `base = median`
- `0.65 <= market_confidence < 0.85` の場合: `base = median * 0.7 + low * 0.3`
- `market_confidence < 0.65` の場合: `base = median * 0.4 + low * 0.6`

## 10. コスト構造

### 10.1 Effective Source Cost
式:
`effective_source_cost = source_price + source_shipping_cost + source_additional_cost`

`source_additional_cost` には以下を含めてよい。
- 代理購入手数料
- 国内転送費
- 梱包材内部消費
- 仕入れ時手数料

### 10.2 Marketplace Fee
式:
`estimated_marketplace_fee = expected_sale_price_base * marketplace_fee_rate + fixed_marketplace_fee`

### 10.3 Payment Cost
式:
`estimated_payment_cost = expected_sale_price_base * payment_fee_rate + fixed_payment_fee`

### 10.4 Outbound Shipping
式:
`estimated_outbound_shipping = shipping_policy.estimated_outbound_shipping`

必要なら condition / size / weight class に応じて分岐してよい。

### 10.5 Packaging / Handling
- `estimated_packaging_cost = packaging_cost_policy or default`
- `estimated_handling_cost = handling_cost_policy or default`

## 11. リスク penalty 設計

### 11.1 Risk Penalty の目的
リスク penalty は、「利益が見えるが事故ると危ない商品」をスコア上で抑えるために使う。

### 11.2 リスクの内訳
- `return_risk_penalty`
- `damage_risk_penalty`
- `authenticity_risk_penalty`
- `restriction_risk_penalty`
- `condition_mismatch_penalty`
- `low_comparable_penalty`

### 11.3 v0.1 合算式
`risk_penalty_total = return_risk_penalty + damage_risk_penalty + authenticity_risk_penalty + restriction_risk_penalty + condition_mismatch_penalty + low_comparable_penalty`

### 11.4 推奨初期ルール
- `comparable_count < 3` → low comparable penalty
- `unsafe_reasons` に `condition_mismatch` → condition penalty
- `unsafe_reasons` に `category_mismatch` → reject 寄り
- ブランド真贋懸念や規制カテゴリ → authenticity / restriction penalty 強
- fragile / bulky 商品 → shipping / damage penalty 強

## 12. Competition / Ambiguity Penalty

### 12.1 Competition Penalty
Phase D の `competition_proxy` を利益式に反映する。

v0.1 例:
- `competition_proxy = low` → `0`
- `competition_proxy = medium` → `base_price * 0.03`
- `competition_proxy = high` → `base_price * 0.08`

### 12.2 Ambiguity Penalty
Candidate 側の ambiguity や review_required を利益に反映する。

式:
`ambiguity_penalty = base_price * ambiguity_penalty_rate`

推奨率:
- ambiguity なし → `0.00`
- 軽微 → `0.03`
- 中程度 → `0.07`
- 強い / review_required → `0.12` 以上

## 13. 中核スコア式

### 13.1 Expected Net Profit
`expected_net_profit = expected_sale_price_base - effective_source_cost - estimated_marketplace_fee - estimated_payment_cost - estimated_outbound_shipping - estimated_packaging_cost - estimated_handling_cost - risk_penalty_total - competition_penalty - ambiguity_penalty`

### 13.2 Margin
`expected_margin = expected_net_profit / expected_sale_price_base`

### 13.3 ROI
`expected_roi = expected_net_profit / effective_source_cost`

### 13.4 Confidence Multiplier
confidence multiplier は利益の見かけ値を減衰させる。

推奨 v0.1 式:
`confidence_multiplier = clamp(0.35, 1.00, market_confidence * 0.55 + category_alignment_score * 0.10 + condition_alignment_score * 0.10 + attribute_alignment_score * 0.10 + comparable_count_factor * 0.10 - ambiguity_penalty_factor * 0.05 - unsafe_penalty_factor * 0.10)`

`comparable_count_factor` は件数を `0.0〜1.0` に正規化する。

### 13.5 Confidence-Adjusted Profit
`confidence_adjusted_profit = expected_net_profit * confidence_multiplier`

## 14. Profitability Score 設計

v0.1 では説明可能性を優先し、絶対利益と比率を混ぜた合成スコアとする。

### 14.1 正規化成分
- `profit_component`
- `margin_component`
- `roi_component`
- `demand_component`
- `confidence_component`
- `risk_penalty_component`

### 14.2 推奨合成式
`profitability_score = (normalized_confidence_adjusted_profit * 0.40 + normalized_margin * 0.20 + normalized_roi * 0.15 + normalized_demand_proxy * 0.10 + normalized_market_confidence * 0.10 - normalized_total_penalty * 0.05) * 100`

補足:
- スコアは `0〜100` を想定
- 正規化方法は deterministic に固定する
- v0.1 では極端な非線形最適化は不要

## 15. 閾値設計

### 15.1 Decision Status
最終判断は以下の 4 段階。
- `launch_now`
- `review_required`
- `watch`
- `reject`

### 15.2 推奨閾値（v0.1）

#### Launch Now
以下をすべて満たす場合:
- `confidence_adjusted_profit >= 3000` 円相当
- `expected_margin >= 0.18`
- `expected_roi >= 0.20`
- `market_confidence >= 0.75`
- `review_required == false`
- 重大 unsafe reason なし

#### Review Required
以下のいずれか:
- `confidence_adjusted_profit >= 1500` だが ambiguity または unsafe reason が残る
- `expected_net_profit` は十分だが confidence が `0.50〜0.75`
- penalty がやや高い
- source / condition / variation の確認が必要

#### Watch
以下のいずれか:
- `confidence_adjusted_profit` はわずかに正
- demand はあるが margin が薄い
- 今すぐ出すほどではないが市場成立性はある
- 価格変動や仕入れ改善待ち

#### Reject
以下のいずれか:
- `expected_net_profit <= 0`
- `confidence_adjusted_profit <= 0`
- `market_confidence < 0.40`
- severe unsafe reason
- 規制 / 真贋 / bundle mismatch / category mismatch が重い

### 15.3 閾値の外部化
各閾値は config / policy で上書き可能にすること。

推奨設定:
- `PROFITABILITY_MIN_LAUNCH_PROFIT`
- `PROFITABILITY_MIN_LAUNCH_MARGIN`
- `PROFITABILITY_MIN_LAUNCH_ROI`
- `PROFITABILITY_MIN_REVIEW_PROFIT`
- `PROFITABILITY_REJECT_CONFIDENCE_THRESHOLD`

## 16. 例外処理

### 16.1 入力欠損
ケース:
- price band 不足
- source cost 未設定
- fee policy 未設定
- shipping policy 未設定
- market evaluation 不在

処理方針:
- silent success 禁止
- `scoring_status = input_incomplete`
- `decision_status = review_required` または `reject`
- `unsafe_reasons` に欠損内容を積む

### 16.2 Market Evaluation が unsafe
ケース:
- `no_results`
- `provider_timeout`
- `too_few_comparables`
- `category_mismatch`

処理方針:
- 利益式は計算できても自動 Launch しない
- `review_required = true` または `reject`
- `confidence_multiplier` を強く下げる

### 16.3 Source Cost が異常
ケース:
- `source_price <= 0`
- `source_shipping_cost < 0`
- 通貨変換不能

処理方針:
- invalid input 扱い
- `scoring_status = invalid_input`
- `decision_status = reject`
- explanation に明記

### 16.4 極端値
ケース:
- 価格帯と source cost が明らかに乖離
- margin > 80% など非現実的

処理方針:
- suspicious outlier として `review_required`
- 必要なら score capped
- `unsafe_reasons += ["suspicious_profit_outlier"]`

### 16.5 Policy 不整合
ケース:
- seller fee profile 取得不可
- shipping profile 不明
- risk policy 不明

処理方針:
- conservative default を使うか、`review_required` に落とす
- デフォルト利用時は evidence に残す

## 17. 永続化

### 17.1 推奨テーブル
- `profitability_scores`
- `profitability_score_components`
- `profitability_score_transitions`（任意）
- `profitability_score_audits`（任意）

### 17.2 保存すべき内容
- 入力スナップショット
- 計算結果
- コンポーネント内訳
- decision status
- review flag
- explanation lines
- config snapshot
- created / updated timestamps

## 18. Orchestrator 統合

### 18.1 新規ジョブ
- `profitability_scoring_job`

### 18.2 入力対象
- `market_evaluation_results` のうち最新かつ有効な candidate
- 必要に応じて seller / environment / review queue で絞る

### 18.3 処理フロー
1. candidate 取得
2. market evaluation 取得
3. source cost / policy 取得
4. profitability input 構築
5. スコア計算
6. decision 判定
7. 永続化
8. JobRun 更新
9. `review_required` / launch候補へ橋渡し

### 18.4 サポートオプション
- `dry_run`
- `limit`
- `seller_account_id`
- `environment`
- `candidate_id`

## 19. Admin CLI / Web

### 19.1 CLI
追加コマンド例:
- `ops profitability run`
- `ops profitability show`
- `ops profitability recent`
- `ops profitability top`
- `ops profitability review`
- `ops profitability unsafe`

表示最低項目:
- candidate id
- expected net profit
- margin
- ROI
- confidence adjusted profit
- decision
- unsafe reasons
- explanation summary

### 19.2 Web
最低画面:
- score list
- score detail
- top opportunity view
- unsafe/review view

表示内容:
- candidate summary
- market summary
- cost breakdown
- net profit / margin / ROI
- confidence multiplier
- decision badge
- unsafe badges
- explanation lines

## 20. 監査・説明責任

- 利益式の各成分を UI / CLI で表示可能にすること
- `decision_reason` は短く要約
- `explanation_lines` は複数行で詳細理由を残すこと
- 人間が「なぜ reject か」「なぜ review_required か」を追えること
- secret や API key は絶対に保存しないこと

## 21. 設定項目

推奨設定例:
- `PROFITABILITY_ENABLED=true|false`
- `PROFITABILITY_RUN_INTERVAL_SECONDS`
- `PROFITABILITY_MIN_LAUNCH_PROFIT`
- `PROFITABILITY_MIN_LAUNCH_MARGIN`
- `PROFITABILITY_MIN_LAUNCH_ROI`
- `PROFITABILITY_MIN_REVIEW_PROFIT`
- `PROFITABILITY_DEFAULT_MARKETPLACE_FEE_RATE`
- `PROFITABILITY_DEFAULT_FIXED_MARKETPLACE_FEE`
- `PROFITABILITY_DEFAULT_PAYMENT_FEE_RATE`
- `PROFITABILITY_DEFAULT_FIXED_PAYMENT_FEE`
- `PROFITABILITY_DEFAULT_PACKAGING_COST`
- `PROFITABILITY_DEFAULT_HANDLING_COST`
- `PROFITABILITY_DEFAULT_LOW_COMPARABLE_PENALTY`
- `PROFITABILITY_DEFAULT_AMBIGUITY_PENALTY_RATE`
- `PROFITABILITY_REJECT_CONFIDENCE_THRESHOLD`

## 22. テスト観点

最低限、以下をテストすること。

1. 正常利益ケースで `launch_now`
2. 利益はあるが ambiguity 高で `review_required`
3. 低利益で `watch`
4. 赤字で `reject`
5. `no_results / too_few_comparables` で confidence 低下
6. source cost 欠損で `input_incomplete`
7. fee policy 欠損で conservative fallback
8. competition high で penalty 増
9. fragile item で damage penalty 増
10. suspicious outlier で `review_required`
11. idempotent rerun
12. dry_run で永続化なし
13. Orchestrator batch 実行
14. CLI `show / recent / top`
15. Web `list / detail`
16. guard / read-only regression
17. full regression suite
