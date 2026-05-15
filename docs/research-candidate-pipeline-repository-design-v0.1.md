# Research Candidate Pipeline / Repository 設計書 v0.1

## 0. 文書目的
`SourceItem` から `ProductCandidate` を生成し、既存の各 Resolver を順次適用して `Research Candidate` 状態まで引き上げるための Pipeline / Repository 層の設計を定義する。

## 1. 主要コンポーネント
- **CandidatePipeline**: 全体のオーケストレーション。各リゾルバの呼び出しと判定、永続化を制御。
- **CandidateBuilder**: 標準化、SKU生成、初期候補モデルの構築。
- **CandidateDecisionEngine**: ビジネスルール（プレバン除外、利益率、スコア等）に基づく最終判定。
- **Repositories**: 
    - `SourceItemRepository`: 仕入れ元データ。
    - `ProductCandidateRepository`: 出品候補データ（SKU管理）。
    - `CandidateEvidenceRepository`: 判定根拠（リゾルバ出力等）。
    - `JobRunRepository`: 実行履歴と統計。

## 2. 処理フロー
1. **SourceItem 読み込み**: 未処理または指定IDのデータを取得。
2. **入口判定**: プレバン強制分岐（manual_preban）、在庫なし除外等。
3. **標準化 & SKU生成**: タイトル正規化と一貫性のあるSKU (`AUTO-XX-YY...`) の発行。
4. **Resolver Orchestration**: 
    - Shipping -> Import -> Selling Fee -> Payout -> Total Cost -> Score
5. **最終判定**: `candidate` (自動出品対象), `excluded` (除外), `review_required` (要目視) を決定。
6. **永続化**: `ProductCandidate` と `CandidateEvidence` を保存。

## 3. SKU 設計
- 形式: `AUTO-{PLATFORM}-{SERIES}-{CHAR}-{PROD}-{ID_HASH}`
- 目的: eBay Inventory API のキーとして利用可能で、再生成時に一貫性を保つこと。

## 4. 判定根拠 (Evidence)
- すべてのリゾルバ出力と判定結果を `CandidateEvidence` として保存する。
- これにより、「なぜこの利益計算になったか」「なぜこのスコアになったか」を後から完全に監査可能にする。

## 5. Idempotency (冪等性)
- 同一の `source_platform + source_item_id` は同一の `candidate` に upsert する。
- すでに出品済み（listed）などの状態にある候補は、このパイプラインで破壊的に上書きしないよう制御する。
