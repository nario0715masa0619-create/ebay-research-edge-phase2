# eBay自動リサーチツール 概要設計 改善版 v0.2

## 0. 文書目的
本書は、プレバンを除く自動化可能商品の収集・標準化・相場照合・利益計算・候補化・将来の eBay 自動出品 / 監視連携までを見据えた、eBay 自動リサーチツールの概要設計を定義するものである。

## 1. 設計原則
- **プレバン分離**: source_platform が pbandai のものは `manual_preban` ラインに強制分岐し、自動出品対象外とする。
- **SKU中心管理**: すべての候補、出品、監視、履歴は SKU を中心に追跡する（eBay Inventory API との親和性）。
- **運用DBとしての候補DB**: リサーチ結果は単なる閲覧用ではなく、将来の `publish readiness` と監視再実行性を持つ運用DBとして設計する。
- **判定根拠の保存**: 除外・候補化判定には必ず reason / evidence / rule version を残す。

## 2. 論理フェーズ
1. **Raw Candidate**: 収集直後の生データ。
2. **Research Candidate**: 標準化、相場照合、利益計算、スコア算出（StandardScoreCalculator）完了。
3. **Listing Ready Candidate**: eBayカテゴリ、Item Specifics、Condition、Policy 等が解決され、出品可能な状態。

## 3. 主要データモデル
- **SourceItem**: 仕入れ元生データ。
- **ProductCandidate**: 標準化・評価・判定後の中心データ。SKU、利益指標、Listing Readiness、判定結果を保持。
- **MonitoringEvent**: 仕入れ元在庫・価格変化や Marketplace 側のエラーを記録するイベントログ。
- **CandidateEvidence**: 判定根拠（Pricing, Shipping, Fee, Score 等の各 Resolver 出力）を保持。
- **RuleConfig**: 利益閾値や高リスクカテゴリ、マッピングテーブルのバージョン管理。

## 4. 状態管理 (Lifecycle)
- **Status**: `collected` -> `normalized` -> `researched` -> `candidate` -> `approved` -> `listing_ready` -> `listed`
- **除外・保留理由**: `exclude_reason` (low_margin, preban等) と `review_reason` (ambiguous_category等) を明確に分離。

## 5. 自動判定ロジック
- **入口判定**: 予約、抽選、発売前、即購入不可品を排除。
- **利益判定**: `AUTO_MIN_RATE` / `AUTO_MIN_PROFIT` を基準に判定。
- **品質判定**: 画像不足、eBayカテゴリ不明、真贋リスク高のものを `manual_review` または `excluded` へ。

## 6. 将来の拡張性
- **Listing Gateway**: eBay Inventory Item / Offer への変換と Publish。
- **Monitoring Engine**: Source (在庫・価格) と Marketplace (出品状態・同期) の二層監視。
