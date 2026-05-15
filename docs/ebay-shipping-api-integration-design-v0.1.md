# eBay送料API接続層 設計書 v0.1

## 1. 目的
本ドキュメントは、eBay Browse API と既存の送料リゾルバ（`shipping/resolver.py`）を接続するための統合レイヤーの設計を定義する。APIレスポンスを直接ロジックに渡さず、中間形式（Snapshot）を介することで、外部API仕様の変更に対する耐性と、テストの容易性を確保する。

## 2. 構成
統合レイヤーは以下の4層で構成される。

1. **Client層 (`browse_client.py`)**: 
   - eBay Browse API (search/getItem) との物理通信を担当。
   - Context Header (EndUserCtx) の付与による正確な送料・税情報の取得をサポート。

2. **Adapter層 (`snapshot_adapters.py`)**:
   - APIレスポンスオブジェクトを、リゾルバが解釈可能な Snapshot (Dict) 形式へ変換。

3. **Pipeline層 (`shipping_pipeline.py`)**:
   - API実行のオーケストレーションを担当。
   - `search` の一次判定に基づき、詳細な `getItem` を実行すべきか判断し、最終的な送料結果を導出する。

4. **Model層 (`models.py`)**:
   - APIレスポンスを扱うための型定義。

## 3. ワークフロー
1. `search_items` または外部から `ItemSummary` を受け取る。
2. `SnapshotAdapter` を使用して Search Snapshot を生成。
3. `should_fetch_detail` により、詳細情報の追加取得が必要か判定。
4. `get_item_with_context` を実行し、詳細な送料・税・返品情報を取得。
5. `resolve_shipping_cost` (Resolver) を呼び出し、正規化された送料結果を得る。

## 4. 設計方針
- **疎結合**: Resolver は API Client を知らず、Snapshot のみを受け取る。
- **耐障害性**: `getItem` (Detail) の取得に失敗した場合でも、`search` の情報を活用して処理を継続する。
- **説明可能性**: Snapshot を経由することで、どのデータに基づき送料が算出されたかのトレースを可能にする。
- **キャリア制約**: 配送キャリアを「FedEx」または「郵便系(Postal)」に限定する。これ以外のキャリア（DHL, UPS等）は原則として除外し、許可キャリアの中から最適なものを選択する。

## 5. 最適化方針
本パイプラインは、eBay Browse API の `getItem` (Detail) 呼び出しを最小限に抑えるように最適化されている。Search Snapshot の内容から、信頼性の高い送料判定が可能と判断された場合は、詳細情報の追加取得をスキップする。

## 6. パイプラインモード
実行時に以下のモードを選択可能：
- **`balanced` (デフォルト)**: 必要時のみ Detail を取得する。
- **`search_only`**: 原則として Detail を取得せず、高速に処理する。
- **`always_detail`**: 常に Detail を取得する（現行互換）。
- **`aggressive_accuracy`**: 精度を優先し、わずかな不確実性でも Detail を取得する。

## 7. Detail 取得の条件 (should_fetch_detail)
以下のいずれかに該当する場合、Detail API の呼び出しを実行する：
1. Search Snapshot または配送オプションが存在しない。
2. 許可キャリア（FedEx/Postal）の候補が見つからない。
3. キャリアが `UNKNOWN` である。
4. 配送サービス名が欠落している。
5. 計算送料 (`CALCULATED`) しか存在しない。
6. 最安値が不許可キャリアであり、許可キャリアの精査が必要。
7. モードが `always_detail` である。

## 8. テスト方針
- Mock Client を使用して、API通信を伴わない Pipeline の結合テストを実施する。
- 各モードにおける API 呼び出し回数と条件分岐の妥当性を検証する。
