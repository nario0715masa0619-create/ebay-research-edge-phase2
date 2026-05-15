# Monitoring / Revise Pipeline 設計書 v0.1

## 0. 文書目的

本書は、eBay に publish 済みの listing を対象として、仕入れ元の在庫・価格・送料・URL 生存と、eBay 側の offer / listing 状態を定期監視し、必要に応じて **価格改定・数量更新・withdraw / pause 相当処理・review 振り分け** を行う `Monitoring / Revise Pipeline` の設計を定義する。

本 Pipeline の目的は、以下を一貫して実現することにある。

- `listed` 商品の source 側変化を継続監視する
- 利益率悪化・在庫切れ・URL 死・政策不整合などを検知する
- eBay Inventory API により価格 / 数量改定を安全に行う
- 必要に応じて listing の終了（withdraw）や review_required 化を行う
- `MonitoringEvent`, `EbayListing`, `ProductCandidate`, `JobRun` に監査可能な形で永続化する
- 自動運用と人手確認の境界を壊さない

eBay Inventory API では、価格 / 数量更新に `bulkUpdatePriceQuantity`、offer 状態確認に `getOffer`、終了に `withdrawOffer` を利用できる。[Source](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item/methods/bulkUpdatePriceQuantity) [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/getOffer) [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/withdrawOffer)

---

## 1. 前提

- `Research Candidate Pipeline`, `Listing Readiness Pipeline`, `eBay Listing Execution Gateway` は既に存在する
- `ProductCandidate.status = listed` の候補と、それに紐づく `EbayListing` が保存されている
- `EbayListing` には最低限 `sku`, `offer_id`, `listing_id`, `marketplace_id`, `listing_price_usd`, `quantity` が保持されている
- 仕入れ元 source の再取得または軽量再確認が可能である
- 価格 / 数量改定は eBay Inventory API 系で行う前提とする
- Inventory API で作成した active listing は、原則として Inventory API 系で改訂・終了を扱う [Source](https://developer.ebay.com/api-docs/sell/static/inventory/pbse-phase2-rest-workflows.html)
- `bulkUpdatePriceQuantity` は Inventory Item の数量、および offer の価格 / 数量更新に利用できる [Source](https://developer.ebay.com/api-docs/sell/static/inventory/bulk-updates.html)

---

## 2. このフェーズの責務

### 2.1 含むもの

- `listed` 商品の監視対象抽出
- source 側在庫、価格、送料、URL 生存の再確認
- eBay 側 offer / listing 状態の同期確認
- 変化差分（price / quantity / availability / margin / URL alive）抽出
- 利益再計算（既存 Resolver / TotalCost / Score の再利用）
- 改定要否判定
- `bulkUpdatePriceQuantity` による価格 / 数量更新
- `withdrawOffer` による listing 終了判断
- `MonitoringEvent` 保存
- `JobRun` 保存
- retry / review / fatal の分類

### 2.2 含まないもの

- source 側自動購入
- multi-channel 同期
- クレーム対応
- 自動 return 処理
- category / aspects の大規模再設計
- eBay 側手動編集との完全双方向同期
- multi-variation item group の本格対応

---

## 3. ゴール

本フェーズ完了時に、以下が成立していることをゴールとする。

- `listed` 商品を定期的に監視できる
- source 価格・在庫変化に応じて利益再計算できる
- 条件に応じて「据え置き / revise / withdraw / review_required」を判定できる
- `bulkUpdatePriceQuantity` による価格 / 数量改定が行える
- `withdrawOffer` による終了が行える
- `MonitoringEvent` と `JobRun` に実行証跡が残る
- duplicate revise / 不要 revise / listed 破壊を防げる

---

## 4. 全体構成

### 4.1 サブコンポーネント

#### 1. MonitoringRevisePipeline
監視・差分判定・改定実行を統括する orchestration 層。

#### 2. MonitoringTargetSelector
監視対象の `listed` 商品を抽出する。

#### 3. SourceStateRefresher
source 側の価格、在庫、送料、URL 生存を再取得 / 再確認する。

#### 4. MarketplaceStateSync
`getOffer` 等により eBay 側の offer / listing 状態を同期する。

#### 5. ProfitRecalculator
変更後 source 情報を用いて既存 Resolver / TotalCost / StandardScore を再実行し、最新利益を算出する。

#### 6. ReviseDecisionEngine
差分と利益条件に基づき、`keep`, `revise_price_quantity`, `set_quantity_zero`, `withdraw`, `review_required` を決定する。

#### 7. PriceQuantityReviseExecutor
`bulkUpdatePriceQuantity` 実行を担当する。

#### 8. WithdrawExecutor
`withdrawOffer` 実行を担当する。

#### 9. MonitoringResultMapper
結果を `ProductCandidate`, `EbayListing`, `MonitoringEvent`, `CandidateEvidence`, `JobRun` に反映する。

#### 10. ReviseRetryClassifier
改定失敗を `retryable`, `review_required`, `fatal` に分類する。

---

## 5. 論理入力 / 出力モデル

### 5.1 MonitoringReviseRequest

- run_id
- candidate_id
- sku
- offer_id
- listing_id
- marketplace_id
- dry_run
- force_recheck
- allow_quantity_zero
- allow_withdraw
- strictness
- max_retry
- monitor_reason

### 5.2 MonitoringReviseResult

- candidate_id
- sku
- monitoring_status
- source_state_status
- marketplace_state_status
- profit_recalculation_status
- revise_action
- revise_status
- withdraw_status
- retryable_flag
- review_required_flag
- monitoring_reason_codes
- error_summary
- evidence_ids
- success_flag

### 5.3 MonitoringReviseBatchResult

- run_id
- processed_count
- keep_count
- revised_count
- zeroed_count
- withdrawn_count
- review_count
- retryable_error_count
- fatal_error_count
- error_summary

---

## 6. 監視対象条件

原則として以下のみを対象とする。

- `ProductCandidate.status == listed`
- `EbayListing.offer_id` が存在する
- `EbayListing.listing_id` が存在するか、少なくとも published 実績がある
- `manual_preban` ではない
- `invalid`, `sold` は通常対象外
- `paused` は設定により対象化可能だが v0.1 では主対象外

---

## 7. 監視ステータス / アクション定義

### 7.1 monitoring_status

- `not_started`
- `running`
- `kept`
- `revised`
- `quantity_zeroed`
- `withdrawn`
- `review_required`
- `retryable_error`
- `failed`
- `skipped`

### 7.2 revise_action

- `keep`
- `revise_price`
- `revise_quantity`
- `revise_price_quantity`
- `set_quantity_zero`
- `withdraw_offer`
- `review_required`

### 7.3 revise_status

- `not_needed`
- `updated`
- `failed`
- `skipped`

### 7.4 withdraw_status

- `not_needed`
- `withdrawn`
- `failed`
- `skipped`

---

## 8. 監視フロー

### 8.1 基本フロー

1. 監視対象抽出
2. source 状態再取得
3. marketplace 状態同期
4. 差分抽出
5. 利益再計算
6. revise decision
7. 必要に応じて `bulkUpdatePriceQuantity`
8. 必要に応じて `withdrawOffer`
9. 結果マッピング
10. `MonitoringEvent` / evidence / `JobRun` 保存

### 8.2 dry_run

`dry_run = true` の場合は API 実行を行わず、以下のみ行う。

- 差分抽出
- 利益再計算
- action 決定
- simulated revise plan 保存
- simulated result 返却

---

## 9. SourceStateRefresher 設計

### 9.1 目的

source 側の最新状態を取得し、listing 継続可否の根拠を得る。

### 9.2 取得対象

- `source_price_jpy`
- `source_shipping_jpy`
- `source_stock_status`
- `source_url_alive`
- 必要に応じて `source_purchase_type`

### 9.3 出力

- `source_state_status`
- `latest_source_price_jpy`
- `latest_source_shipping_jpy`
- `latest_source_stock_status`
- `source_url_alive`
- `source_diff_summary`

### 9.4 代表差分

- `price_up`
- `price_down`
- `shipping_up`
- `shipping_down`
- `out_of_stock`
- `url_dead`

---

## 10. MarketplaceStateSync 設計

### 10.1 目的

eBay 側の現在状態を同期し、offer / listing が期待通り存在・継続しているか確認する。

### 10.2 対象 API

- `getOffer`

`getOffer` は published / unpublished offer の状態確認に利用できる [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/getOffer)

### 10.3 出力

- `marketplace_state_status`
- `offer_exists`
- `offer_state`
- `listing_exists`
- `current_marketplace_price`
- `current_marketplace_quantity`
- `marketplace_diff_summary`

### 10.4 代表差分

- `offer_missing`
- `listing_missing`
- `price_mismatch`
- `quantity_mismatch`
- `offer_unexpected_state`

---

## 11. ProfitRecalculator 設計

### 11.1 目的

source 側の変化後に利益・スコアを最新化し、listing 継続可否を判定する。

### 11.2 再利用コンポーネント

- ShippingResolver
- ImportChargeResolver
- SellingFeeResolver
- PayoutFeeResolver
- TotalCostResolver
- StandardScoreCalculator

### 11.3 出力

- `updated_expected_profit_jpy`
- `updated_expected_profit_rate`
- `updated_standard_score`
- `profit_recalculation_status`
- `profit_reason_codes`

### 11.4 方針

- 既存ロジックを再実装しない
- source 差分反映後の候補価格・送料・数量前提で再評価する
- 再計算結果は candidate / evidence に保存する

---

## 12. ReviseDecisionEngine 設計

### 12.1 目的

source 差分と利益再計算結果をもとに、listing を維持・改定・終了・review のどれにするか決定する。

### 12.2 主判定軸

- source 在庫あり / なし
- source URL 生存
- 最新利益率
- 最新利益額
- 最新スコア
- marketplace 価格差分
- marketplace 数量差分
- 価格変化閾値
- 高リスク判定

### 12.3 基本ルール

- source 在庫切れ -> `set_quantity_zero` または `withdraw_offer`
- source URL dead -> `withdraw_offer` または `review_required`
- 利益率が閾値割れ -> `set_quantity_zero` または `withdraw_offer`
- source 価格上昇で利益悪化 -> `revise_price` または `withdraw_offer`
- source 価格低下で利益改善 -> `revise_price` を許可
- source / eBay quantity 不整合 -> `revise_quantity`
- 曖昧・危険 -> `review_required`

### 12.4 出力

- `revise_action`
- `decision_reason_codes`
- `review_required_flag`
- `withdraw_recommended_flag`

---

## 13. PriceQuantityReviseExecutor 設計

### 13.1 目的

eBay listing の価格 / 数量を安全に更新する。

### 13.2 対象 API

- `bulkUpdatePriceQuantity`

この API は Inventory Item の ship-to-home quantity および offer の価格 / 数量更新に利用できる。[Source](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item/methods/bulkUpdatePriceQuantity)

### 13.3 入力

- sku
- offer_id
- target_price
- target_quantity
- marketplace_id

### 13.4 出力

- `revise_status`
- `updated_price`
- `updated_quantity`
- `response_payload`
- `error_summary`

### 13.5 方針

- 必要差分がない場合は実行しない
- price のみ、quantity のみ、両方を区別する
- quantity 0 への更新は seller 側の out-of-stock 運用方針に従う
- request / response は evidence 保存する

eBay には quantity 0 を out-of-stock として維持する運用概念があるが、運用方針により withdraw を優先する場合もある。[Source](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/out-of-stock-operation.html)

---

## 14. WithdrawExecutor 設計

### 14.1 目的

継続不適切な listing を終了する。

### 14.2 対象 API

- `withdrawOffer`

`withdrawOffer` は single-variation listing の終了に利用できる。[Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/withdrawOffer)

### 14.3 実行条件例

- source 在庫切れが継続
- URL 死
- 利益率大幅悪化
- 高リスク状態
- quantity 0 維持より終了が適切

### 14.4 出力

- `withdraw_status`
- `withdrawn_listing_id`
- `response_payload`
- `error_summary`

---

## 15. MonitoringResultMapper 設計

### 15.1 目的

監視 / 改定結果を DB と evidence に反映する。

### 15.2 `ProductCandidate` 更新項目

- `source_price_jpy`
- `source_shipping_jpy`
- `source_stock_status`
- `expected_profit_jpy`
- `expected_profit_rate`
- `standard_score`
- `status`
- `last_checked_at`
- `updated_at`
- `decision_reason_codes`

### 15.3 `EbayListing` 更新項目

- `listing_price_usd`
- `quantity`
- `offer_status`
- `inventory_item_status`
- `updated_at`
- `last_publish_error` または `last_revise_error`
- 必要に応じて paused / withdrawn 相当状態

### 15.4 `MonitoringEvent` 保存項目

- event_scope
- event_type
- before_value
- after_value
- action_taken
- created_at

### 15.5 代表 `action_taken`

- `keep`
- `revise_price`
- `revise_quantity`
- `revise_price_quantity`
- `set_quantity_zero`
- `withdraw_offer`
- `review_required`

---

## 16. ReviseRetryClassifier 設計

### 16.1 目的

改定 / withdraw 失敗を再試行可能か、人手確認が必要か、致命的かに分類する。

### 16.2 分類

- `retryable`
- `review_required`
- `fatal`

### 16.3 代表例

#### retryable
- timeout
- 5xx
- 一時的 API 障害

#### review_required
- location / policy 整合不良
- offer 状態不整合
- quantity zero 運用条件不一致
- source / eBay 不整合が大きい

#### fatal
- `offer_id` 欠損
- `listing_id` 欠損かつ同期不能
- invalid status
- manual_preban 混入
- draft / execution 前提欠損

---

## 17. Idempotency / 重複防止

### 17.1 単位

- candidate 単位
- sku 単位
- offer 単位
- run_id 単位

### 17.2 ルール

- 同一 run 内で同一 SKU を二重改定しない
- 差分がない場合は revise しない
- 既に withdrawn 済みなら重複 withdraw しない
- 既に quantity 0 で維持中なら無駄な 0 更新を繰り返さない
- dry_run は状態を破壊しない
- `force_recheck=True` でも不要 API 実行は避ける

---

## 18. JobRun 設計

### 18.1 保存項目

- run_id
- job_name
- job_scope
- started_at
- finished_at
- status
- processed_count
- keep_count
- revised_count
- zeroed_count
- withdrawn_count
- review_count
- retryable_error_count
- fatal_error_count
- error_summary

### 18.2 ステータス例

- `running`
- `completed`
- `completed_with_errors`
- `failed`

---

## 19. Evidence 永続化方針

### 19.1 保存対象

最低限、以下を `CandidateEvidence` に保存する。

- source_state_refresh
- marketplace_state_sync
- profit_recalculation
- revise_decision
- revise_request
- revise_response
- withdraw_request
- withdraw_response
- retry_classification
- monitoring_result

### 19.2 evidence_payload 方針

- request / response snapshot を JSON 保存
- token など機密値は保存しない
- run_id, timestamp, rule_version を含める
- before / after を明示する
- dry_run の場合は simulated action plan を保存する

---

## 20. 状態遷移設計

### 20.1 代表遷移

- `listed -> listed` 維持
- `listed -> paused` 将来拡張
- `listed -> invalid` URL死などの特例時のみ
- `listed -> candidate` へ無条件巻き戻ししない
- `listed -> withdrawn` 相当管理（status または listing 側 state で表現）
- `listed -> review_required相当` は candidate status を壊さず reason を追加

### 20.2 保護方針

- sold を誤って revise しない
- invalid を自動復旧しない
- manual_preban を混入させない
- listing 実績を破壊しない

---

## 21. 対象ファイル案

- `docs/monitoring-revise-pipeline-design-v0.1.md`
- `src/monitoring/models.py`
- `src/monitoring/pipeline.py`
- `src/monitoring/target_selector.py`
- `src/monitoring/source_refresher.py`
- `src/monitoring/marketplace_sync.py`
- `src/monitoring/profit_recalculator.py`
- `src/monitoring/revise_decision_engine.py`
- `src/monitoring/revise_executor.py`
- `src/monitoring/withdraw_executor.py`
- `src/monitoring/result_mapper.py`
- `src/monitoring/retry_classifier.py`
- `tests/test_monitoring_revise_pipeline.py`

必要に応じて修正可:
- `src/ebay/api_client.py`
- `src/ebay/models.py`
- `src/repositories/ebay_listing_repository.py`
- `src/repositories/job_run_repository.py`
- `src/repositories/candidate_evidence_repository.py`

---

## 22. 推奨関数シグネチャ

    def monitor_and_revise_listing(
        candidate_id: str,
        run_id: str | None = None,
        marketplace_id: str = "EBAY_US",
        dry_run: bool = False,
        force_recheck: bool = False,
        allow_quantity_zero: bool = True,
        allow_withdraw: bool = True,
        strictness: str = "balanced",
        max_retry: int = 1,
        timeout_seconds: int = 30,
    ):
        ...

    def run_monitoring_revise_pipeline(
        candidate_ids: list[str] | None = None,
        limit: int | None = None,
        marketplace_id: str = "EBAY_US",
        dry_run: bool = False,
        force_recheck: bool = False,
        strictness: str = "balanced",
    ):
        ...

---

## 23. テストケース案（10件）

1. `listed` 以外の候補が監視対象外になる
2. source 在庫切れで `set_quantity_zero` または `withdraw_offer` が選ばれる
3. source URL 死で `withdraw_offer` または `review_required` になる
4. source 価格上昇で利益率閾値割れなら revise / withdraw 判定になる
5. source 価格低下で revise_price が選ばれる
6. `bulkUpdatePriceQuantity` が price / quantity 差分に応じて実行される
7. `withdrawOffer` 成功で withdrawn 相当状態が保存される
8. `getOffer` 同期失敗が retryable または review_required に分類される
9. `dry_run` で API 実行せず simulated action を返す
10. 同一 run で同一 SKU の duplicate revise を防ぐ

可能なら追加:
11. quantity 0 維持済みの listing を再度 0 更新しない
12. `MonitoringEvent` が before / after 付きで保存される
13. `JobRun` 件数が正しく集計される

---

## 24. 完了条件

この設計に基づく実装が以下を満たせば、本フェーズは完了とみなす。

- `listed` 商品を監視できる
- source / marketplace 差分を取得できる
- 利益再計算できる
- `keep / revise / withdraw / review_required` を決定できる
- `bulkUpdatePriceQuantity` を安全に実行できる
- `withdrawOffer` を安全に実行できる
- `MonitoringEvent` と evidence を保存できる
- dry_run を実装できる
- idempotency が成立する
- 既存テストを壊さず pytest が pass する
