# eBay Listing Execution Gateway 設計書 v0.1

## 0. 文書目的

本書は、`Listing Ready Candidate` を入力として受け取り、eBay Inventory API を用いて `Inventory Item` 作成 / 更新、`Offer` 作成 / 更新、`Publish` 実行までを担う `eBay Listing Execution Gateway` の設計を定義する。

本 Gateway の目的は、以下を一貫して実現することにある。

- `Listing Ready Candidate` を実際の eBay 出品処理へ接続する
- `inventory_item_draft` / `offer_draft` を eBay API 実行単位へ変換する
- `createOrReplaceInventoryItem -> createOffer -> publishOffer` の実行順を厳格に管理する
- 成功 / 失敗 / 再試行 / review 必要状態を `EbayListing` と監査ログへ永続化する
- 再実行可能で、かつ二重 publish を防ぐ実行基盤を構築する

eBay の単品出品フローは `createOrReplaceInventoryItem`、`createOffer`、`publishOffer` の順で構成される [Source](https://developer.ebay.com/api-docs/sell/static/inventory/inventory-item-to-offer.html)

---

## 1. 前提

- `Research Candidate Pipeline` と `Listing Readiness Pipeline` は既に存在し、対象候補は `listing_readiness_status = ready` または `review_required` 相当の情報を持つ
- `inventory_item_draft` と `offer_draft` は内部ドラフトとして保持されている
- publish 対象は原則として `pipeline_type == auto` かつ `publish_readiness == true` の候補に限定する
- eBay で offer publish を行うには、business policies と inventory location が必要である [Source](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)
- inventory location は `merchantLocationKey` により参照され、必要に応じて `createInventoryLocation` / `getInventoryLocations` により管理される [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/location/methods/createInventoryLocation) [Source](https://developer.ebay.com/api-docs/sell/static/inventory/managing-inventory-locations.html)
- Inventory API で作成した listing は、以後も原則として Inventory API 系で改訂・終了を扱う [Source](https://developer.ebay.com/api-docs/sell/static/inventory/pbse-phase2-rest-workflows.html)

---

## 2. このフェーズの責務

### 2.1 含むもの

- `Listing Ready Candidate` の読み込み
- 実行前ガード（publish readiness / status / idempotency / duplicate publish 防止）
- `inventory_item_draft` から `createOrReplaceInventoryItem` 実行
- `offer_draft` から `createOffer` 実行、または既存 offer 更新方針の管理
- `publishOffer` 実行
- eBay 応答の `offerId` / `listingId` / 実行結果を `EbayListing` へ保存
- 実行ログ / API 応答 / error を evidence / execution log として保存
- retry 対象と review 対象の切り分け
- 実行件数・成功件数・失敗件数を `JobRun` に記録

### 2.2 含まないもの

- category / aspects / readiness の再解決
- source 側在庫監視
- marketplace 監視バッチ
- price revise / quantity revise の本格運用
- withdraw / end listing の完全運用
- multi-variation item group の本格対応
- policy / location 自動作成フローの完全自動化

---

## 3. ゴール

本フェーズ完了時に、以下が成立していることをゴールとする。

- `Listing Ready Candidate` を eBay Inventory API 実行へ接続できる
- `Inventory Item -> Offer -> Publish` が順序通り実行される
- `EbayListing` に `offer_id`, `listing_id`, `inventory_item_status`, `offer_status` が保存される
- 実行失敗時に `last_publish_error` と reason を保存できる
- 二重 publish を防止できる
- `JobRun` と evidence により実行監査ができる

---

## 4. 全体構成

### 4.1 サブコンポーネント

#### 1. ListingExecutionGateway
Listing 実行全体の orchestration を担当する。

#### 2. CandidateExecutionGuard
publish 対象可否、status 保護、duplicate publish 防止、必須データ確認を行う。

#### 3. InventoryItemExecutor
`createOrReplaceInventoryItem` 実行を担当する。

#### 4. OfferExecutor
`createOffer` 実行、または既存 offer の再利用 / 更新方針を担当する。

#### 5. PublishExecutor
`publishOffer` 実行を担当する。

#### 6. ExecutionResultMapper
API 応答を `EbayListing` / evidence / execution log に反映する。

#### 7. RetryClassifier
失敗内容を `retryable`, `review_required`, `fatal` に分類する。

#### 8. ListingExecutionRepository Adapter
`ProductCandidate`, `EbayListing`, `CandidateEvidence`, `JobRun` を更新する。

#### 9. EbayInventoryApiClient
eBay Sell Inventory API のラッパー。  
最低限、Inventory Item / Offer / Publish / GetOffer / Withdraw の拡張余地を持つ。

---

## 5. 論理入力 / 出力モデル

### 5.1 ListingExecutionRequest

- candidate_id
- run_id
- marketplace_id
- dry_run
- force_republish
- create_location_if_missing
- strictness
- max_retry
- timeout_seconds

### 5.2 ListingExecutionResult

- candidate_id
- sku
- execution_status
- inventory_item_status
- offer_status
- publish_status
- offer_id
- listing_id
- execution_reason_codes
- retryable_flag
- review_required_flag
- error_summary
- evidence_ids
- success_flag

### 5.3 ListingExecutionBatchResult

- run_id
- processed_count
- success_count
- skipped_count
- retryable_error_count
- review_required_count
- fatal_error_count
- error_summary

---

## 6. 実行対象条件

本 Gateway は原則として以下の候補のみを対象にする。

- `pipeline_type == auto`
- `listing_readiness_status == ready`
- `publish_readiness == true`
- `status in approved, listing_ready, candidate`
- `manual_preban` ではない
- `invalid`, `sold` は対象外
- 既に `listed` である場合は通常は skip、明示的な revise / republish 方針時のみ例外

---

## 7. 実行ステータス定義

### 7.1 execution_status

- `not_started`
- `running`
- `succeeded`
- `partial_success`
- `retryable_error`
- `review_required`
- `failed`
- `skipped`

### 7.2 inventory_item_status

- `not_created`
- `created`
- `updated`
- `failed`

### 7.3 offer_status

- `not_created`
- `created`
- `existing_reused`
- `failed`

### 7.4 publish_status

- `not_published`
- `published`
- `failed`
- `skipped`

---

## 8. 実行フロー

### 8.1 基本フロー

1. candidate 読み込み
2. execution guard 実行
3. inventory item payload 検証
4. `createOrReplaceInventoryItem`
5. offer payload 検証
6. `createOffer`
7. `publishOffer`
8. 応答マッピング
9. `EbayListing` 保存
10. evidence 保存
11. `ProductCandidate.status` / listing metadata 更新
12. `JobRun` 更新

### 8.2 dry_run

`dry_run = true` の場合は API 実行を行わず、以下のみ行う。

- guard
- payload validation
- blocker 確認
- execution plan 生成
- evidence 保存
- simulated result 返却

---

## 9. CandidateExecutionGuard 設計

### 9.1 目的

不正 / 危険 / 重複な実行を事前に防ぐ。

### 9.2 チェック項目

- `pipeline_type == auto`
- `listing_readiness_status == ready`
- `publish_readiness == true`
- `inventory_item_draft` が存在する
- `offer_draft` が存在する
- `merchantLocationKey` が存在する、または default / create strategy で解決可能
- `paymentPolicyId`, `returnPolicyId`, `fulfillmentPolicyId` が存在する
- 既に `listed` で duplicate publish にならない
- `offer_id` 既存時の扱いが明確
- `listing_id` 既存時の扱いが明確

### 9.3 代表 blocker

- `candidate_not_ready`
- `publish_readiness_false`
- `missing_inventory_item_draft`
- `missing_offer_draft`
- `missing_location`
- `missing_policy_ids`
- `already_listed`
- `manual_preban_not_allowed`
- `invalid_candidate_status`

---

## 10. InventoryItemExecutor 設計

### 10.1 目的

`inventory_item_draft` を eBay Inventory Item API へ送信する。

### 10.2 対象 API

- `createOrReplaceInventoryItem`

この call は SKU をキーに inventory item record を作成または置換する [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item/methods/createOrReplaceInventoryItem)

### 10.3 入力

- sku
- availability
- condition
- product.title
- product.description
- product.aspects
- product.imageUrls

### 10.4 出力

- success / fail
- inventory_item_status
- response metadata
- error summary
- request snapshot

### 10.5 方針

- 同一 SKU なら upsert 相当で扱う
- publish 前に必ず inventory item を先行作成 / 更新する
- request / response は evidence 保存する

---

## 11. OfferExecutor 設計

### 11.1 目的

`offer_draft` を eBay offer に変換する。

### 11.2 対象 API

- `createOffer`
- 将来拡張: `getOffer` による既存 offer 確認

`getOffer` は特定 offer の published / unpublished 状態確認に利用できる [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/getOffer)

### 11.3 入力

- sku
- marketplaceId
- format
- categoryId
- availableQuantity
- pricingSummary.price
- listingDuration
- merchantLocationKey
- listingPolicies

### 11.4 出力

- offer_id
- offer_status
- success / fail
- error summary
- request snapshot

### 11.5 方針

- 基本は毎回 `createOffer`
- 将来は既存 unpublished offer 再利用の余地を残す
- `offer_id` は `EbayListing` に保存する

---

## 12. PublishExecutor 設計

### 12.1 目的

生成済み offer を実際の eBay listing に変換する。

### 12.2 対象 API

- `publishOffer`

publishOffer は offer を active listing 化する [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/publishOffer)

### 12.3 方針

- `offer_id` が存在する場合のみ実行
- 成功時は `listing_id` を回収し `EbayListing` に保存
- 失敗時は error code / message / domain / category を保存
- duplicate publish 防止のため既存 listed 状態を guard する

### 12.4 注意点

- publish には business policies と `merchantLocationKey` が必要 [Source](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)
- invalid inventory location など location / policy 不備は retry ではなく review が適切な場合がある [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/publishOffer)

---

## 13. ExecutionResultMapper 設計

### 13.1 目的

各 API 応答を `ProductCandidate`, `EbayListing`, `CandidateEvidence`, `JobRun` に反映する。

### 13.2 `EbayListing` 反映項目

- sku
- inventory_item_status
- offer_id
- offer_status
- listing_id
- marketplace_id
- listing_price_usd
- quantity
- merchant_location_key
- fulfillment_policy_id
- payment_policy_id
- return_policy_id
- last_publish_attempt_at
- last_publish_error
- listed_at
- updated_at

### 13.3 `ProductCandidate` 反映項目

- status
- updated_at
- publish_readiness
- listing_blockers
- decision_reason_codes
- last_checked_at

### 13.4 status 例

- publish 成功 -> `listed`
- retryable error -> `approved` 維持または execution status のみ更新
- review required -> `approved` または `candidate` 維持 + review reason 追加
- fatal error -> `approved` 維持 + failure evidence 追加

---

## 14. RetryClassifier 設計

### 14.1 目的

API エラーを再試行可能か、人手確認が必要か、致命的かに分類する。

### 14.2 分類

- `retryable`
- `review_required`
- `fatal`

### 14.3 代表例

#### retryable
- 一時的 network / timeout
- 5xx
- eBay 側一時 application error

#### review_required
- missing policy
- invalid location
- category / condition / aspects の整合不良
- offer payload の業務不足
- 既存 listing 競合

#### fatal
- candidate not ready
- manual_preban
- 必須 draft 欠損
- 不正 marketplace / 不正 payload の構造エラー

### 14.4 出力

- `retryable_flag`
- `review_required_flag`
- `error_classification`
- `execution_reason_codes`

---

## 15. Idempotency / 重複防止

### 15.1 単位

- candidate 単位
- SKU 単位
- listing 単位
- run_id 単位

### 15.2 ルール

- 同一 candidate に対する二重 publish を防ぐ
- 既に `listing_id` が存在し `status == listed` の場合、通常は skip
- `force_republish = true` の場合のみ例外的に再実行可能
- `createOrReplaceInventoryItem` は upsert 前提で扱う
- `offer_id` が既存なら再利用 / 再作成方針を明示する
- 同一 run 内で同一 SKU を二重処理しない

### 15.3 監査

- skip / create / publish / retry / fail をすべて evidence / job metrics に残す

---

## 16. JobRun 設計

### 16.1 保存項目

- run_id
- job_name
- job_scope
- started_at
- finished_at
- status
- processed_count
- success_count
- skipped_count
- retryable_error_count
- review_required_count
- fatal_error_count
- error_summary

### 16.2 ステータス例

- `running`
- `completed`
- `completed_with_errors`
- `failed`

---

## 17. Evidence 永続化方針

### 17.1 保存対象

最低限、以下を `CandidateEvidence` に保存する。

- execution_guard
- inventory_item_request
- inventory_item_response
- offer_request
- offer_response
- publish_request
- publish_response
- retry_classification
- execution_decision

### 17.2 evidence_payload 方針

- API request / response snapshot を JSON 保存
- token や機密値は保存しない
- error code / message / domain / category を保持
- run_id, timestamp, rule_version を保持
- dry_run の場合は simulated payload と判定理由を保存

---

## 18. `EbayListing` と候補状態の関係

### 18.1 候補が publish 成功した場合

- `ProductCandidate.status = listed`
- `EbayListing.offer_id` 保存
- `EbayListing.listing_id` 保存
- `EbayListing.offer_status = published` 相当
- `EbayListing.inventory_item_status = created/updated`

### 18.2 失敗時

- publish 失敗でも `ProductCandidate` を即 invalid にしない
- `review_required` 相当なら blocker / reason を追加
- retryable なら再試行対象として保持
- `last_publish_error` を `EbayListing` に残す

---

## 19. 将来拡張との接続点

本 Gateway は将来的に以下へ拡張可能であること。

- `bulkUpdatePriceQuantity` による価格 / 数量更新 [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item/methods/bulkUpdatePriceQuantity)
- `withdrawOffer` による listing 終了 [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/withdrawOffer)
- `getOffer` による状態同期 [Source](https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/getOffer)
- inventory location 自動作成 / 同期 [Source](https://developer.ebay.com/api-docs/sell/static/inventory/managing-inventory-locations.html)

---

## 20. 対象ファイル案

- `docs/ebay-listing-execution-gateway-design-v0.1.md`
- `src/listing_execution/models.py`
- `src/listing_execution/gateway.py`
- `src/listing_execution/guard.py`
- `src/listing_execution/inventory_item_executor.py`
- `src/listing_execution/offer_executor.py`
- `src/listing_execution/publish_executor.py`
- `src/listing_execution/result_mapper.py`
- `src/listing_execution/retry_classifier.py`
- `src/ebay/api_client.py`
- `tests/test_ebay_listing_execution_gateway.py`

必要に応じて修正可:
- `src/ebay/models.py`
- `src/repositories/product_candidate_repository.py`
- `src/repositories/candidate_evidence_repository.py`
- `src/repositories/job_run_repository.py`

---

## 21. 推奨関数シグネチャ

    def execute_listing_candidate(
        candidate_id: str,
        run_id: str | None = None,
        marketplace_id: str = "EBAY_US",
        dry_run: bool = False,
        force_republish: bool = False,
        create_location_if_missing: bool = False,
        strictness: str = "balanced",
        max_retry: int = 1,
        timeout_seconds: int = 30,
    ):
        ...

    def run_listing_execution_gateway(
        candidate_ids: list[str] | None = None,
        limit: int | None = None,
        marketplace_id: str = "EBAY_US",
        dry_run: bool = False,
        force_republish: bool = False,
        strictness: str = "balanced",
    ):
        ...

---

## 22. テストケース案（10件）

1. `listing_readiness_status != ready` の候補が guard で skip / block される
2. `manual_preban` 候補が実行対象外になる
3. `inventory_item_draft` 欠損で失敗する
4. `offer_draft` 欠損で失敗する
5. 正常系で `createOrReplaceInventoryItem -> createOffer -> publishOffer` 順に実行される
6. publish 成功で `offer_id` と `listing_id` が `EbayListing` に保存される
7. location / policy 不足で `review_required` に分類される
8. 一時的 API エラーで `retryable_error` に分類される
9. `dry_run` で API 実行せず simulated result を返す
10. 既に `listed` の候補を duplicate publish しない

可能なら追加:
11. `force_republish=True` で再実行を許可
12. execution evidence が全段階保存される
13. `JobRun` 件数が正しく集計される

---

## 23. 完了条件

この設計に基づく実装が以下を満たせば、本フェーズは完了とみなす。

- `Listing Ready Candidate` を eBay Inventory API 実行へ接続できる
- `createOrReplaceInventoryItem -> createOffer -> publishOffer` が順に実行される
- `EbayListing` に実行結果を保存できる
- duplicate publish を防止できる
- retry / review / fatal を分類できる
- evidence を保存できる
- dry_run を実装できる
- idempotency が成立する
- 既存テストを壊さず pytest が pass する
