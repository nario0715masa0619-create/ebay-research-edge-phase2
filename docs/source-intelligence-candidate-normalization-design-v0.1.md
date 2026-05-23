# Source Intelligence / Candidate Normalization 設計書 v0.1

## 1. 目的

本レイヤの目的は、複数の仕入れ元・商品ソースから取得した生データを、**比較可能で利益評価可能な単位へ正規化し、同一商品または近似商品を安定的に束ねること**である。

このプロジェクト全体の本当の目的は「安全に出品すること」ではなく、**爆益になりやすい商品を自動で継続発見すること**である。  
そのために本レイヤは、後続の `Market Evaluation`、`Profitability Scoring`、`Opportunity Ranking` が正しく機能するための最重要土台となる。

本レイヤは、単なる文字列整形ではない。  
本質は、**「このソース商品は何者なのか」を機械的に安定して定義し、eBay 上で比較・評価できる canonical な商品候補へ落とし込むこと**にある。

---

## 2. ゴール

本レイヤのゴールは以下である。

1. 複数ソースの商品情報を、比較可能な canonical 形式へ正規化できること
2. JAN / GTIN / UPC / EAN / Brand / MPN / Model / Title を用いて同一商品または近似商品をマッチングできること
3. bundle / lot / set / variation / color / size / capacity 違いを検知し、誤マッチを減らせること
4. マッチの強さを `match_confidence` として数値化できること
5. 曖昧な候補を `review_required` / `ambiguity_flags` として分離できること
6. 後続の Profitability Scoring に必要な入力特徴量を保持できること
7. seller / marketplace / category ごとに後続評価へ流し込めること
8. source-specific な汚れたデータを吸収し、監査可能な evidence を残せること
9. dry-run / batch 実行 / scheduler 実行に耐えること
10. 永続化・再評価・再クラスタリングに対応できること

---

## 3. 北極星との関係

このレイヤは、プロジェクトの北極星である

> 安く仕入れられて、eBay では高く・早く・安定して売れ、しかも競争がまだ緩い商品を、自動で見つけ続けること

を実現するための**最初の本丸**である。

なぜなら、同一商品判定が崩れると以下がすべて壊れるためである。

- eBay 価格比較
- 競合数の近似
- 売れ行き推定
- カテゴリ適合性評価
- condition 比較
- 利益計算
- リスク判定

したがって本レイヤは、**Discover first, operate second** の原則において `Discover` 側の最初の中核を担う。

---

## 4. スコープ

### 4.1 本レイヤに含むもの
- source item の取り込み
- source-specific attribute extraction
- タイトル正規化
- identifier 抽出
- brand / model / mpn / product code 抽出
- variation / bundle / lot / set 判定
- canonical identity 生成
- 同一商品クラスタリング
- match confidence 算出
- ambiguity flag 付与
- canonical candidate 生成
- evidence / explanation の保存
- 後続スコアリング入力 feature の保持
- dry-run / review_required / idempotency
- 永続リポジトリ対応

### 4.2 本レイヤに含まないもの
- eBay 市場価格の本格評価
- 競合強度の最終判定
- 売れ行きの最終推定
- 利益スコアの最終計算
- 自動出品判断
- revise / withdraw 判断
- 高度な ML モデルの導入
- 画像ベース類似検索
- 外部 LLM を用いた高コスト正規化

---

## 5. 設計原則

### 5.1 Normalize first, score later
先に「この商品は何か」を安定化し、その後に価格・利益・競争を評価する。

### 5.2 Exact match より safe match
誤った強結合より、曖昧な候補を review に回す方が良い。  
誤マッチは後続の利益判定を壊すため、安全側に倒す。

### 5.3 Explainable normalization
なぜその canonical candidate に紐づいたのか説明できること。  
`matched_on_identifiers`、`title_similarity`、`variation_penalties` などの evidence を必ず残す。

### 5.4 Source-aware but source-agnostic output
入力ソースごとの差異は吸収するが、出力は source に依存しない canonical 形式に統一する。

### 5.5 Confidence-aware pipeline
一致・不一致の二値ではなく、`match_confidence` と `ambiguity_flags` を中心に扱う。

### 5.6 Idempotent and re-runnable
同一 source item を再処理しても結果が暴れないこと。  
ルール改良後の再正規化にも耐えられること。

### 5.7 Feature preservation for scoring
後続の Profitability Scoring で必要になる特徴量は、この時点で捨てずに保持する。

---

## 6. 全体アーキテクチャ内での位置づけ

本プロジェクトの利益創出レイヤは以下の順で整理する。

1. **Source Intelligence Layer**
2. **Market Evaluation Layer**
3. **Profitability Scoring Layer**
4. **Opportunity Ranking Layer**
5. **Execution & Operations Layer**

本設計書は、このうち **Source Intelligence Layer** の中核である  
**Candidate Normalization** を定義する。

---

## 7. 主なユースケース

1. 国内フリマAと中古ショップBから取得した同一商品を 1 つの canonical candidate に束ねる
2. タイトルは似ているが「セット品」と「単品」を分離する
3. 型番がハイフンあり / なしで表記ゆれしていても同一候補へ寄せる
4. JAN がある商品は高 confidence で同定する
5. JAN がなくても Brand + MPN + Model + Title 類似で near-match として扱う
6. 色違い・サイズ違い・容量違いを variation として分離する
7. MPN が同じでも condition や bundle 構成が異なれば ambiguity を立てる
8. 曖昧な候補を review_required に送る
9. 既知 canonical candidate に新規 source item を紐づける
10. ルール更新後に過去 source item を再正規化する

---

## 8. 入力・出力の考え方

### 8.1 入力
入力は各ソースから収集された `RawSourceItem` であり、内容は sourceごとに大きく揺れる。

例:
- title
- description
- source_url
- source_platform
- price
- shipping_price
- seller_name
- seller_rating
- images
- condition_text
- quantity_text
- raw_attributes
- scraped_identifiers
- raw_category
- raw_brand
- raw_model
- raw_mpn
- raw_gtin

### 8.2 出力
出力は以下の二層とする。

1. **NormalizedSourceItem**
   - source item を正規化した中間表現
2. **CanonicalProductCandidate**
   - 比較・評価・後続スコアリングのための canonical 商品候補

---

## 9. 新規作成ファイル

- `docs/source-intelligence-candidate-normalization-design-v0.1.md`
- `src/discovery/models.py`
- `src/discovery/attribute_extractor.py`
- `src/discovery/title_normalizer.py`
- `src/discovery/identifier_normalizer.py`
- `src/discovery/variation_detector.py`
- `src/discovery/entity_matcher.py`
- `src/discovery/match_confidence.py`
- `src/discovery/source_aggregator.py`
- `src/discovery/candidate_normalizer.py`
- `src/discovery/review_flagger.py`
- `src/discovery/result_mapper.py`
- `src/discovery/bootstrap.py`
- `src/repositories/persistent_normalized_source_item_repository.py`
- `src/repositories/persistent_canonical_candidate_repository.py`
- `src/repositories/persistent_match_evidence_repository.py`
- `tests/test_candidate_normalization.py`
- `tests/test_entity_matcher.py`
- `tests/test_variation_detector.py`
- `tests/test_match_confidence.py`

---

## 10. 修正想定ファイル

- `src/db/models.py`
- `src/db/bootstrap.py`
- `src/repositories/*`
- `src/orchestrator/job_definitions.py`
- `src/orchestrator/bootstrap.py`
- `src/admin_cli/app.py`
- `src/admin_cli/bootstrap.py`
- `src/admin_web/routes/*`（将来の一覧/詳細/レビュー画面）
- 既存の `research` / `candidate` / `pipeline` 関連モジュール
- Alembic migration ファイル群

---

## 11. ドメインモデル

### 11.1 RawSourceItem
ソースからそのまま取得した生アイテム。

主な項目:
- `source_item_id: str`
- `source_platform: str`
- `source_url: str`
- `seller_account_id: str | None`
- `environment_type: str | None`
- `raw_title: str`
- `raw_description: str | None`
- `raw_price: Decimal | None`
- `raw_shipping_price: Decimal | None`
- `raw_condition_text: str | None`
- `raw_quantity_text: str | None`
- `raw_brand: str | None`
- `raw_model: str | None`
- `raw_mpn: str | None`
- `raw_gtin: str | None`
- `raw_category: str | None`
- `raw_attributes: dict`
- `image_urls: list[str]`
- `seller_meta: dict`
- `scraped_at: datetime`

### 11.2 NormalizedSourceItem
後続比較に使えるよう整形した source item。

主な項目:
- `normalized_item_id: str`
- `source_item_id: str`
- `normalized_title: str`
- `normalized_brand: str | None`
- `normalized_model: str | None`
- `normalized_mpn: str | None`
- `normalized_gtins: list[str]`
- `normalized_condition: str | None`
- `normalized_quantity: int | None`
- `variation_keys: dict`
- `bundle_flags: list[str]`
- `parsed_attributes: dict`
- `identity_signals: dict`
- `normalization_flags: list[str]`
- `review_required: bool`
- `created_at: datetime`
- `updated_at: datetime`

### 11.3 ProductIdentity
商品同定に使う canonical identity。

主な項目:
- `brand: str | None`
- `model: str | None`
- `mpn: str | None`
- `gtins: list[str]`
- `product_line: str | None`
- `variation_signature: str | None`
- `bundle_signature: str | None`
- `condition_family: str | None`

### 11.4 MatchEvidence
なぜマッチしたか/しなかったかの根拠。

主な項目:
- `evidence_id: str`
- `normalized_item_id: str`
- `candidate_id: str | None`
- `identifier_hits: dict`
- `title_similarity_score: float`
- `brand_match_score: float`
- `model_match_score: float`
- `mpn_match_score: float`
- `variation_penalty: float`
- `bundle_penalty: float`
- `condition_penalty: float`
- `ambiguity_flags: list[str]`
- `explanation_lines: list[str]`
- `created_at: datetime`

### 11.5 CanonicalProductCandidate
後続評価に使う canonical 商品候補。

主な項目:
- `candidate_id: str`
- `canonical_title: str`
- `canonical_brand: str | None`
- `canonical_model: str | None`
- `canonical_mpn: str | None`
- `canonical_gtins: list[str]`
- `canonical_condition_family: str | None`
- `variation_signature: str | None`
- `bundle_signature: str | None`
- `source_count: int`
- `matched_source_item_ids: list[str]`
- `match_confidence: float`
- `ambiguity_flags: list[str]`
- `review_required: bool`
- `category_candidates: list[str]`
- `feature_payload: dict`
- `created_at: datetime`
- `updated_at: datetime`

### 11.6 NormalizationResult
1 source item の正規化結果。

主な項目:
- `source_item_id: str`
- `normalized_item: NormalizedSourceItem`
- `candidate: CanonicalProductCandidate | None`
- `evidence: MatchEvidence`
- `status: str`
- `review_required: bool`
- `errors: list[str]`

---

## 12. 正規化で扱う主要概念

### 12.1 Exact Identity Signals
強い一致根拠。
- JAN
- GTIN
- UPC
- EAN
- 正規化済み MPN
- 強い型番完全一致

### 12.2 Soft Identity Signals
補助的な一致根拠。
- title 類似
- brand 類似
- model 類似
- product line 類似
- category 近似
- attributes 近似

### 12.3 Variation Signals
誤結合防止の鍵。
- color
- size
- capacity
- storage
- edition
- bundle count
- lot count
- region/version
- included accessories

### 12.4 Ambiguity Signals
人手確認が必要な兆候。
- title は近いが GTIN 不一致
- Brand 一致 + MPN 欠損 + タイトル曖昧
- 単品 / セット混在
- variation 値が矛盾
- capacity/size が複数候補
- 型番の一部欠損

---

## 13. 処理フロー

### 13.1 全体フロー
1. `RawSourceItem` を受け取る
2. `attribute_extractor` が source-specific な属性を抽出
3. `title_normalizer` がタイトルを整形
4. `identifier_normalizer` が GTIN / JAN / MPN / Model を正規化
5. `variation_detector` が color / size / capacity / bundle を抽出
6. `NormalizedSourceItem` を生成
7. `entity_matcher` が既存 canonical candidate と照合
8. `match_confidence` を算出
9. `review_flagger` が review_required / ambiguity flags を付与
10. `source_aggregator` が新規 candidate 生成または既存 candidate に統合
11. `MatchEvidence` とともに保存
12. `NormalizationResult` を返す

### 13.2 照合優先順位
1. GTIN / JAN / UPC / EAN 完全一致
2. Brand + MPN 強一致
3. Brand + Model + Variation 強一致
4. Title 類似 + Brand 補強 + Category 補強
5. Soft match のみの場合は review または新規 candidate

---

## 14. タイトル正規化ルール

### 14.1 基本整形
- 全角/半角統一
- 大文字/小文字の標準化
- 不要記号の除去
- 連続空白の圧縮
- ハイフン/スラッシュの正規化
- 「新品」「中古」「送料無料」など source noise の分離

### 14.2 除去対象例
- セール文言
- 感嘆符多用
- 絵文字
- 過剰な状態説明
- 出品者都合の販促文
- 「即購入OK」「早い者勝ち」等

### 14.3 保持すべき要素
- ブランド名
- 型番
- モデル名
- 容量
- サイズ
- 色
- セット数量
- エディション情報

---

## 15. Identifier 正規化ルール

### 15.1 GTIN 系
- ハイフン/空白除去
- 数字以外の除外
- 複数候補の配列保持
- 不正長は flag 付与
- JAN/UPC/EAN の種別推定

### 15.2 MPN / Model
- 大文字化
- 空白/ハイフン揺れ吸収
- 接尾辞・接頭辞の noise 分離
- source 特有表記を統一
- 似ているが別物になりやすい suffix を保持

### 15.3 Brand
- 既知 alias の正規化
- OEM / generic / unbranded の扱い統一
- 大文字小文字揺れ吸収

---

## 16. Variation / Bundle / Lot 判定

### 16.1 Variation として扱うもの
- color
- size
- capacity
- storage
- region/version
- edition
- pattern
- accessory pack differences

### 16.2 Bundle / Lot として扱うもの
- 2個セット
- まとめ売り
- lot
- bulk
- with accessories
- 本体のみ / 箱付き / 付属品あり

### 16.3 誤結合回避ルール
- 単品とセット品は原則別 candidate
- 容量違いは原則別 candidate
- 色違いは variation-aware に分離
- 付属品差が大きい場合は別 candidate 寄りに扱う
- condition 差だけで別 candidate にはしないが、必要に応じて penalty を持つ

---

## 17. Match Confidence の考え方

`match_confidence` は 0.0 ~ 1.0 の連続値で表現する。

### 17.1 加点要素
- GTIN exact hit
- Brand + MPN exact hit
- 高 title similarity
- category の近さ
- variation 整合
- source 間で複数一致シグナル

### 17.2 減点要素
- variation 矛盾
- bundle 不一致
- title ambiguity
- GTIN 不一致
- MPN 部分一致のみ
- condition family 矛盾
- attributes 欠損

### 17.3 例
- `>= 0.95`: auto-merge 可
- `0.80 ~ 0.95`: merge 候補、条件付き
- `0.60 ~ 0.80`: review_required
- `< 0.60`: 新規 candidate または reject

この閾値は設定可能にする。

---

## 18. Review Required の条件

以下のいずれかで `review_required = true` とする。

- 複数 candidate へ近いスコアでマッチ
- identifier が欠損し soft match のみ
- variation / bundle / lot が曖昧
- 容量/サイズ違いの疑い
- source 情報が不足
- GTIN と title が矛盾
- Brand + Model は近いが MPN が異なる
- 既存 candidate の canonical identity と矛盾

---

## 19. Canonical Candidate の生成ルール

### 19.1 新規生成
以下の場合、新規 `CanonicalProductCandidate` を作成する。
- 既存 candidate への十分な match がない
- soft match しかなく、安全に統合できない
- variation / bundle が既存と異なる
- ambiguity が強い

### 19.2 既存候補への統合
以下の場合、既存 candidate に source item を追加する。
- exact identity signal 一致
- variation signature 一致
- ambiguity が閾値以下
- review 不要

### 19.3 Canonical 属性更新
複数 source からの情報で canonical を更新する際は、安全側ルールを採用する。
- GTIN は union
- brand は最頻値 or highest-confidence source
- title は最も情報量が高くノイズの少ないもの
- variation / bundle は矛盾時に review flag

---

## 20. Profitability Scoring へ渡す入力契約

本レイヤでは Profitability Scoring の完全実装は行わないが、以下の入力 feature を保持する。

### 20.1 必須入力候補
- `source_cost_total`
- `source_shipping_cost`
- `condition_family`
- `category_candidates`
- `category_confidence`
- `match_confidence`
- `ambiguity_flags`
- `variation_signature`
- `bundle_signature`
- `identity_strength`
- `source_count`
- `seller_quality_signals`
- `risk_flags`

### 20.2 将来の Market Evaluation 用入力
- `ebay_search_keywords_seed`
- `brand`
- `model`
- `mpn`
- `gtins`
- `canonical_title`
- `attribute_payload`

---

## 21. 永続化設計

### 21.1 新規テーブル候補
1. `normalized_source_items`
2. `canonical_product_candidates`
3. `match_evidences`
4. `candidate_source_links`

### 21.2 主なカラム
#### normalized_source_items
- `normalized_item_id`
- `source_item_id`
- `normalized_title`
- `normalized_brand`
- `normalized_model`
- `normalized_mpn`
- `normalized_gtins_json`
- `normalized_condition`
- `variation_keys_json`
- `bundle_flags_json`
- `parsed_attributes_json`
- `normalization_flags_json`
- `review_required`
- `created_at`
- `updated_at`

#### canonical_product_candidates
- `candidate_id`
- `canonical_title`
- `canonical_brand`
- `canonical_model`
- `canonical_mpn`
- `canonical_gtins_json`
- `canonical_condition_family`
- `variation_signature`
- `bundle_signature`
- `source_count`
- `match_confidence`
- `ambiguity_flags_json`
- `review_required`
- `category_candidates_json`
- `feature_payload_json`
- `created_at`
- `updated_at`

#### match_evidences
- `evidence_id`
- `normalized_item_id`
- `candidate_id`
- `identifier_hits_json`
- `title_similarity_score`
- `brand_match_score`
- `model_match_score`
- `mpn_match_score`
- `variation_penalty`
- `bundle_penalty`
- `condition_penalty`
- `ambiguity_flags_json`
- `explanation_lines_json`
- `created_at`

### 21.3 インデックス候補
- `normalized_source_items(source_item_id)` UNIQUE
- `canonical_product_candidates(canonical_mpn)`
- `canonical_product_candidates(canonical_brand, canonical_model)`
- `canonical_product_candidates(variation_signature)`
- `canonical_product_candidates(review_required, updated_at)`
- `match_evidences(normalized_item_id)`
- `match_evidences(candidate_id)`

---

## 22. Repository インターフェース

### 22.1 NormalizedSourceItemRepository
- `save(normalized_item)`
- `upsert(normalized_item)`
- `get_by_source_item_id(source_item_id)`
- `list_recent(limit=100)`
- `list_review_required(limit=100)`

### 22.2 CanonicalCandidateRepository
- `save(candidate)`
- `upsert(candidate)`
- `get_by_candidate_id(candidate_id)`
- `find_by_gtin(gtin)`
- `find_by_brand_mpn(brand, mpn)`
- `find_by_brand_model(brand, model)`
- `search_similar_titles(normalized_title, limit=20)`
- `list_review_required(limit=100)`

### 22.3 MatchEvidenceRepository
- `save(evidence)`
- `list_by_candidate_id(candidate_id)`
- `list_by_normalized_item_id(normalized_item_id)`

---

## 23. Orchestrator 統合

本レイヤの batch 実行 job を追加する。

### 23.1 推奨 job 名
- `source_intelligence_normalization_job`

### 23.2 役割
- 未正規化 source item を取得
- batch 正規化
- candidate 統合
- review_required 生成
- 結果を保存
- JobRun を更新

### 23.3 推奨引数
- `seller_account_id: str | None`
- `environment_type: str | None`
- `limit: int | None`
- `dry_run: bool = False`
- `force_recheck: bool = False`
- `source_platform: str | None`

### 23.4 JobRun に残すべき件数
- `processed_count`
- `normalized_count`
- `merged_count`
- `new_candidate_count`
- `review_required_count`
- `skipped_count`
- `error_count`

---

## 24. Admin CLI / Web 連携（将来前提）

### 24.1 Admin CLI
将来的に以下のコマンドを提供できる構造にする。
- `ops discovery normalize run`
- `ops discovery normalize recent`
- `ops discovery normalize review`
- `ops discovery candidate show --candidate-id ...`
- `ops discovery candidate search --brand ... --mpn ...`
- `ops discovery candidate merge-review`

### 24.2 Admin Web
将来的に以下を提供できる構造にする。
- Normalized Items 一覧
- Review Required 一覧
- Candidate detail
- Match evidence 表示
- Manual approve / reject / split / merge 補助

---

## 25. エラーハンドリング方針

- source item が壊れていても batch 全体は止めない
- identifier 抽出失敗は fatal ではなく flag 化
- 既存 candidate 競合時は review に送る
- repository 書き込み失敗は retryable / fatal を分類
- dry_run では永続化しないが decision は返す
- 不整合は `ambiguity_flags` と `explanation_lines` に残す

---

## 26. セキュリティ / データ品質

- source に含まれる不要な個人情報は canonical candidate に持ち込まない
- seller 名や連絡先等は後続利益評価に不要であれば feature payload に含めない
- 生データは保持しても、後続レイヤには必要最小限だけ流す
- 正規化ルールは source-specific hack を過剰に埋め込まず、拡張可能構造にする

---

## 27. テストケース

1. GTIN 完全一致で同一 candidate に統合
2. Brand + MPN 一致で high confidence
3. Title 類似のみで review_required
4. セット品と単品を分離
5. 色違いを variation として分離
6. 容量違いを分離
7. ハイフン違い MPN を同一視
8. GTIN 不一致で merge 抑止
9. brand alias 正規化
10. title noise 除去
11. bundle detection
12. lot detection
13. ambiguity_flags 付与
14. evidence explanation 生成
15. 既存 candidate 更新
16. 新規 candidate 生成
17. idempotent 再実行
18. dry_run で永続化なし
19. review_required 一覧抽出
20. source 欠損値を安全処理
21. condition 差 penalty
22. category seed の保持
23. feature payload 保持
24. partial source corruption に耐える
25. JobRun 件数が正しい

---

## 28. 段階的実装方針

### Phase A
- models
- title normalization
- identifier normalization
- basic matcher
- confidence scoring
- repositories
- tests

### Phase B
- variation detector
- bundle / lot detection
- review flagger
- evidence enrichment
- orchestrator job

### Phase C
- admin review tooling
- manual merge/split support
- higher-quality alias dictionaries
- scoring contract integration

---

## 29. 完了条件

1. `RawSourceItem -> NormalizedSourceItem -> CanonicalProductCandidate` の流れが動作する
2. exact/soft/ambiguous match を区別できる
3. `match_confidence` が計算される
4. `review_required` が安全側に機能する
5. evidence が保存される
6. canonical candidate が永続化される
7. dry-run / batch 実行に対応する
8. Orchestrator から実行できる
9. Profitability Scoring 向け feature contract が保持される
10. 全 pytest PASS

---

## 30. 制約

- v0.1 では画像照合を前提にしない
- v0.1 では外部高コスト AI 依存を避ける
- v0.1 では deterministic rule-based matching を優先する
- full fuzzy matching を先にやりすぎない
- 無理に auto-merge 率を上げず、安全側を優先する

---

## 31. 推奨コミットメッセージ

Add Source Intelligence and Candidate Normalization layer

---

## 32. 最終報告必須項目

- 作成 / 修正ファイル一覧
- 新規 models / normalizers / matcher / repositories 一覧
- 正規化ルール要約
- match confidence / review_required の設計要約
- 永続化テーブル概要
- orchestrator 統合内容
- テスト一覧と結果
- Alembic revision ID
- コミットハッシュ
- main への push 成功可否

---

## 33. リポジトリ

- GitHub: `https://github.com/nario0715masa0619-create/ebay-research-edge-phase2`
- Local: `D:\AI_スクリプト成果物\ebay-research-edge-phase2`

---

## 34. 関連する eBay API 上の前提

後続の `Market Evaluation Layer` や `Execution Layer` との接続を見据え、本レイヤの canonical candidate は eBay API で比較・検索しやすい形を目指す。

- Browse API はキーワード・カテゴリなどで商品検索や item summary 取得に利用できる [Source](https://developer.ebay.com/api-docs/buy/browse/overview.html)
- Browse API の search は比較対象候補の取得に使える [Source](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search)
- Taxonomy API は適切なカテゴリや item aspects の取得に使える [Source](https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html)
- getItemAspectsForCategory によりカテゴリごとの必要/推奨 item specifics を確認できる [Source](https://developer.ebay.com/api-docs/commerce/taxonomy/resources/category_tree/methods/getItemAspectsForCategory)
- Inventory API は canonical candidate から inventory item / offer 管理につなげる後段の基盤となる [Source](https://developer.ebay.com/api-docs/sell/inventory/overview.html)

---

## 35. 結論

本レイヤは、単に source item を整形するための補助機能ではない。  
本質は、**複数ソースから得た曖昧な商品情報を、利益評価可能な canonical な商品候補へ変換することで、爆益商品の自動発見を成立させること**にある。

今後の設計判断は次の問いに従う。

> この正規化は、爆益候補をより正確に見つけることに寄与するか。

Yes なら進める。  
No なら優先度を下げる。  
それが本レイヤの設計思想である。
