# Listing Readiness Pipeline 設計書 v0.1

## 0. 文書目的

本書は、`Research Candidate` を入力として受け取り、eBay 出品に必要なメタデータ、カテゴリ、condition、item specifics、画像品質、タイトル/説明、policy / location 連携前提、publish blockers を評価し、`Listing Ready Candidate` 状態まで引き上げるための `Listing Readiness Pipeline` の設計を定義する。

本 Pipeline の目的は、以下を一貫して実現することにある。

- `Research Candidate` と `Listing Ready Candidate` を明確に分離する
- 利益が出る候補と、実際に eBay へ安全に出品可能な候補を区別する
- category / condition / aspects / title / image / policy 依存の不足を blockers として可視化する
- `listing_readiness_status` と `publish_readiness` を候補DBへ永続化する
- 将来の `createOrReplaceInventoryItem -> createOffer -> publishOffer` に自然に接続できる構造を用意する

eBay の単品出品フローは `createOrReplaceInventoryItem -> createOffer -> publishOffer` であり、publish 前には inventory item 情報、offer 情報、business policies、inventory location が必要になる [Source](https://developer.ebay.com/api-docs/sell/static/inventory/inventory-item-to-offer.html)

---

## 1. 前提

- `Research Candidate Pipeline` は既に存在し、`ProductCandidate` に利益、スコア、evidence、基本正規化結果が保存されている
- 本フェーズでは actual publish は行わず、publish 可能性の評価と不足情報の抽出までを扱う
- 本フェーズは `manual_preban` を自動出品対象に含めない
- eBay category 候補は `getCategorySuggestions` により補助可能であるが、category 決定だけで publish readiness は確定しない [Source](https://developer.ebay.com/api-docs/commerce/taxonomy/resources/category_tree/methods/getCategorySuggestions)
- item specifics は category ごとに required / recommended / optional があり、required aspect 未充足では listing readiness は完成しない [Source](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/item-specifics.html)
- publish には fulfillment / payment / return policy と inventory location が必要である [Source](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)

---

## 2. このフェーズの責務

### 2.1 含むもの

- `Research Candidate` の読み込み
- eBay category 候補の評価 / 確定支援
- category に対する required aspects / recommended aspects の評価
- `ebay_aspects_json` の整備
- `missing_required_aspects` の抽出
- condition / condition descriptor の解決
- title / description / image readiness の評価
- policy / location 参照情報の解決可能性評価
- publish blockers の抽出
- `listing_readiness_status` と `publish_readiness` の決定
- `CandidateEvidence` への readiness 根拠保存
- 将来の listing payload 生成へ接続可能なデータ整形

### 2.2 含まないもの

- 実際の Inventory Item 作成
- Offer 作成
- Publish 実行
- business policy の eBay API 自動作成
- inventory location の eBay API 自動作成
- 実際の revise / end / pause
- marketplace 監視

---

## 3. ゴール

本フェーズ完了時に、以下が成立していることをゴールとする。

- `ProductCandidate` ごとに `listing_readiness_status` が確定している
- `publish_readiness` が true / false で説明可能に決定されている
- `listing_blockers` が列挙されている
- `ebay_category_id`、`ebay_condition`、`ebay_aspects_json`、`missing_required_aspects` が候補に反映されている
- title / description / image / policy / location の不足が evidence として保存されている
- 将来の Inventory Item / Offer payload に変換可能な下地ができている

---

## 4. 全体構成

### 4.1 サブコンポーネント

#### 1. ListingReadinessPipeline
`Research Candidate` から `Listing Ready Candidate` 相当状態を構築する orchestration 層。

#### 2. CategoryResolver
候補タイトル / 正規化情報をもとに eBay category 候補を決定・評価する。

#### 3. AspectsResolver
category に基づき required / recommended aspects を評価し、`ebay_aspects_json` と不足項目を作る。

#### 4. ConditionResolver
source condition を eBay condition / condition descriptor へ変換する。

#### 5. ContentReadinessEvaluator
title、description、image_urls の出品品質を評価する。

#### 6. PolicyReadinessEvaluator
fulfillment / payment / return policy と merchant location が解決済みか、あるいはデフォルト参照可能かを評価する。

#### 7. BlockerEngine
不足・曖昧・危険要素を `listing_blockers` として統合する。

#### 8. ListingPayloadDraftBuilder
publish はしないが、Inventory Item / Offer に近い内部ドラフト構造を生成する。

#### 9. ListingReadinessRepository Adapter
`ProductCandidate` 更新と evidence 保存を仲介する。

---

## 5. 論理入力 / 出力モデル

### 5.1 ListingReadinessRequest

- candidate_id
- run_id
- force_recheck
- marketplace_id
- category_tree_id
- strictness
- allow_default_policy_reference
- allow_incomplete_recommended_aspects
- title_max_length
- description_template_version

### 5.2 ListingReadinessResult

- candidate_id
- sku
- listing_readiness_status
- publish_readiness
- ebay_category_id
- ebay_condition
- ebay_aspects_json
- missing_required_aspects
- missing_recommended_aspects
- listing_blockers
- readiness_reason_codes
- evidence_ids
- inventory_item_draft
- offer_draft
- success_flag

### 5.3 ListingReadinessBatchResult

- run_id
- processed_count
- ready_count
- blocked_count
- review_count
- error_count
- error_summary

---

## 6. listing_readiness_status 定義

### 6.1 状態

- `not_checked`
- `checking`
- `blocked`
- `review_required`
- `ready`

### 6.2 意味

- `not_checked`: readiness 未評価
- `checking`: 評価中
- `blocked`: publish 不能な不足あり
- `review_required`: 自動確定には危険だが、人手確認で通せる可能性あり
- `ready`: publish 前提の主要要件を満たす

### 6.3 publish_readiness

- `true`: 主要 blockers がなく publish 前提の主要要件が揃っている
- `false`: 1つ以上の重大 blocker がある

---

## 7. 入力候補条件

本 Pipeline は原則として以下の候補にのみ適用する。

- `pipeline_type == auto`
- `decision_type == candidate` または `review_required`
- `status in candidate, approved, researched`
- `manual_preban` ではない
- `invalid`, `sold`, `listed` を主対象にしない

### 例外

- `force_recheck=True` の場合、`candidate` 以外も再評価可能
- ただし `listed` に対する破壊的上書きは禁止する

---

## 8. CategoryResolver 設計

### 8.1 目的

- `ProductCandidate` の標準化済み情報から eBay category を決定する
- `ebay_category_id`
- `category_confidence`
- `category_reason_codes`
- `category_tree_id`
- `category_tree_version`

を候補へ反映する

### 8.2 入力材料

- normalized_title
- brand
- series
- character
- product_type
- source_title
- 既存 `ebay_category_id`
- category mapping table
- marketplace_id

### 8.3 出力

- 確定 category
- 候補 category 群
- confidence
- reasons
- review 要否

### 8.4 方針

- 既存 category mapping があればそれを優先
- mapping が不十分なら category suggestion を用いて候補を補強
- confidence が低い場合は `review_required`
- category 未解決は `blocked`

`getCategorySuggestions` は category 候補の relevance 順返却に使えるが、Sandbox では実用的でないため本番想定で扱う [Source](https://developer.ebay.com/api-docs/commerce/taxonomy/resources/category_tree/methods/getCategorySuggestions)

---

## 9. AspectsResolver 設計

### 9.1 目的

category ごとに必要な item specifics を判定し、候補が eBay 出品に必要な属性を満たすかを評価する。

### 9.2 出力

- `ebay_aspects_json`
- `missing_required_aspects`
- `missing_recommended_aspects`
- `aspects_confidence`
- `aspects_reason_codes`

### 9.3 方針

- required aspects が1つでも不足 -> `blocked`
- recommended aspects 不足のみ -> `ready` または `review_required`
- aspect 値の自動生成根拠は evidence に残す
- multi-value aspect が必要な場合に備え、配列保存可能な構造にする

eBay では category ごとに required / recommended / optional aspects が存在するため、内部データは可変構造を前提にする [Source](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/item-specifics.html)

---

## 10. ConditionResolver 設計

### 10.1 目的

source 側 condition から eBay condition を解決する。

### 10.2 出力

- `ebay_condition`
- `condition_descriptor_json`
- `condition_confidence`
- `condition_reason_codes`

### 10.3 方針

- mapping table により解決する
- category 依存で condition が変わる可能性を考慮する
- 曖昧な場合は `review_required`
- condition 未解決は `blocked`

---

## 11. ContentReadinessEvaluator 設計

### 11.1 title 評価

最低限評価すること。

- title が存在する
- 過度に短すぎない
- 出品に必要な主要語が含まれる
- marketplace の title 制約に概ね収まる
- 露骨なノイズ・無意味語が多くない

### 11.2 description 評価

- 生成可能である
- 必須情報を含められる
- source 依存の危険表現や不正確な断定を含まない
- テンプレート生成可能

### 11.3 image 評価

- image_urls が最低必要枚数を満たす
- 画像URLが有効
- 主要商品画像が存在する
- 画像不足は `review_required` または `blocked`

### 11.4 出力

- `content_readiness_status`
- `title_ready`
- `description_ready`
- `image_ready`
- `content_blockers`
- `content_reason_codes`

---

## 12. PolicyReadinessEvaluator 設計

### 12.1 目的

publish 前提で必要な business policies と inventory location の参照可能性を評価する。

### 12.2 必要参照

- `fulfillment_policy_id`
- `payment_policy_id`
- `return_policy_id`
- `merchant_location_key`

### 12.3 方針

- candidate 自体に未保持でも、設定値や seller defaults で解決可能なら `ready`
- デフォルト参照も不可なら `blocked`
- 一部未解決だが人手で埋めやすいなら `review_required`

publish には payment / return / fulfillment policy と inventory location が必要 [Source](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)

---

## 13. BlockerEngine 設計

### 13.1 目的

個別評価器の結果を統合し、publish readiness の阻害要因を明示化する。

### 13.2 blocker 種別例

- `category_unresolved`
- `category_low_confidence`
- `required_aspects_missing`
- `condition_unresolved`
- `condition_low_confidence`
- `title_not_ready`
- `description_not_ready`
- `insufficient_images`
- `policy_unresolved`
- `location_unresolved`
- `manual_preban_not_supported`
- `high_risk_candidate`
- `invalid_candidate_status`

### 13.3 出力

- `listing_blockers`
- `readiness_reason_codes`
- `listing_readiness_status`
- `publish_readiness`

### 13.4 判定ルール

- 重大 blocker あり -> `blocked`
- blocker はないが confidence 低い / 曖昧 -> `review_required`
- 重大 blocker なし -> `ready`

---

## 14. ListingPayloadDraftBuilder 設計

### 14.1 目的

publish はしないが、内部的に Inventory Item / Offer へ変換しやすいドラフト構造を作る。

### 14.2 inventory_item_draft

最低限以下を保持可能にする。

- sku
- availability.shipToLocationAvailability.quantity
- condition
- product.title
- product.description
- product.aspects
- product.imageUrls

### 14.3 offer_draft

最低限以下を保持可能にする。

- sku
- marketplaceId
- format
- categoryId
- availableQuantity
- pricingSummary.price
- listingDuration
- merchantLocationKey
- listingPolicies
  - paymentPolicyId
  - returnPolicyId
  - fulfillmentPolicyId

これらは publish 時に必要になる主要要素と整合させる [Source](https://developer.ebay.com/api-docs/sell/static/inventory/publishing-offers.html)

---

## 15. Evidence 永続化方針

### 15.1 保存対象

最低限、以下を `CandidateEvidence` として保存する。

- category_mapping
- aspects_resolution
- condition_mapping
- content_readiness
- policy_readiness
- blocker_evaluation
- listing_payload_draft
- listing_readiness_decision

### 15.2 evidence_payload 方針

- rule_version を含める
- confidence / status / notes / reason_codes を落とさない
- category tree version を含める
- required aspect 不足一覧を含める
- draft payload は redact 不要範囲のみ保存する

---

## 16. ProductCandidate 反映項目

本 Pipeline は最低限、以下を `ProductCandidate` に反映する。

- `ebay_category_id`
- `category_tree_id`
- `category_tree_version`
- `category_confidence`
- `ebay_condition`
- `condition_confidence`
- `ebay_aspects_json`
- `missing_required_aspects`
- `listing_readiness_status`
- `listing_blockers`
- `publish_readiness`
- `decision_reason_codes`
- `last_checked_at`
- `updated_at`

必要に応じて以下も保持する。

- `condition_descriptor_json`
- `missing_recommended_aspects`
- `inventory_item_draft_json`
- `offer_draft_json`

---

## 17. 状態遷移設計

### 17.1 基本遷移

- `candidate -> approved`
- `approved -> listing_ready`
- `candidate -> review_required相当`
- `candidate -> blocked相当`
- `listing_ready -> listing_ready` 再評価可

### 17.2 status / readiness の関係

- `status` は全体業務状態
- `listing_readiness_status` は出品準備状態

例:
- `status = candidate`, `listing_readiness_status = blocked`
- `status = approved`, `listing_readiness_status = ready`

### 17.3 禁止方針

- `listed` を readiness pipeline が巻き戻さない
- publish 関連IDをこのフェーズで作らない
- `manual_preban` を `ready` にしない

---

## 18. Idempotency / 再評価方針

### 18.1 単位

- candidate 単位
- run_id 単位
- marketplace 単位

### 18.2 ルール

- 同一 candidate に対しては upsert 更新する
- `force_recheck=False` の場合、既に `ready` かつ blocker なしなら再計算をスキップ可能
- `force_recheck=True` の場合は evidence 再生成を許可する
- 既存 publish 系フィールドは破壊しない

---

## 19. 対象ファイル案

- `docs/listing-readiness-pipeline-design-v0.1.md`
- `src/listing_readiness/models.py`
- `src/listing_readiness/pipeline.py`
- `src/listing_readiness/category_resolver.py`
- `src/listing_readiness/aspects_resolver.py`
- `src/listing_readiness/condition_resolver.py`
- `src/listing_readiness/content_evaluator.py`
- `src/listing_readiness/policy_evaluator.py`
- `src/listing_readiness/blocker_engine.py`
- `src/listing_readiness/draft_builder.py`
- `tests/test_listing_readiness_pipeline.py`

必要に応じて修正可:
- `src/ebay/models.py`
- `src/research_pipeline/models.py`
- `src/repositories/product_candidate_repository.py`
- `src/repositories/candidate_evidence_repository.py`

---

## 20. 推奨関数シグネチャ

    def build_listing_readiness(
        candidate_id: str,
        run_id: str | None = None,
        force_recheck: bool = False,
        marketplace_id: str = "EBAY_US",
        category_tree_id: str | None = None,
        strictness: str = "balanced",
        allow_default_policy_reference: bool = True,
        allow_incomplete_recommended_aspects: bool = True,
    ):
        ...

    def run_listing_readiness_pipeline(
        candidate_ids: list[str] | None = None,
        limit: int | None = None,
        force_recheck: bool = False,
        marketplace_id: str = "EBAY_US",
        strictness: str = "balanced",
    ):
        ...

---

## 21. テストケース案（10件）

1. `manual_preban` 候補が `ready` にならず block される
2. category 解決成功で `ebay_category_id` が埋まる
3. category 未解決で `category_unresolved` blocker が立つ
4. required aspects 不足で `blocked` になる
5. recommended aspects のみ不足なら `review_required` になる
6. condition 解決失敗で `condition_unresolved` blocker が立つ
7. image 不足で `insufficient_images` が立つ
8. default policy reference により policy readiness が通る
9. inventory_item_draft / offer_draft が生成される
10. 同一 candidate 再実行で upsert され重複作成されない

可能なら追加:
11. `force_recheck=True` で evidence 再生成
12. `listed` status を readiness pipeline が破壊しない
13. title / description readiness 失敗で review になる

---

## 22. 完了条件

この設計に基づく実装が以下を満たせば、本フェーズは完了とみなす。

- `Research Candidate` から `listing_readiness_status` を決定できる
- `publish_readiness` を決定できる
- category / condition / aspects / content / policy / location の readiness を評価できる
- `listing_blockers` を保存できる
- `CandidateEvidence` に根拠を保存できる
- `inventory_item_draft` / `offer_draft` を生成できる
- idempotency が成立する
- 既存テストを壊さず pytest が pass する
