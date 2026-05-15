# TotalCostResolver 設計書 v0.1

## 1. 目的
本設計書は、既存の各コスト resolver (Shipping, ImportCharge, SellingFee, PayoutFee) の結果を統合し、商品1件あたりの総コスト、最終利益、利益率、ROI を説明可能に算出する TotalCostResolver の仕様を定義する。

## 2. 基本方針
TotalCostResolver は、各 resolver の出力を信頼して受け取り、それらを整合的に束ねる。個別リゾルバのロジックは再実装せず、データの集約と指標の計算に集中する。

## 3. 主要指標の計算式
- **売上総額 (Gross Sale ex Tax)**: `(sale_item_price * quantity) + buyer_charged_shipping`
- **仕入れ着地原価 (Landed Procurement Cost)**: `(procurement_item_cost * quantity) + shipping_cost + import_cost`
- **総コスト (Total Cost)**: `landed_procurement_cost + selling_fee + payout_fee + additional_costs`
- **最終利益 (Final Profit)**: `gross_sale_ex_tax - total_cost`
- **利益率 (Margin Rate)**: `final_profit / gross_sale_ex_tax`
- **ROI**: `final_profit / landed_procurement_cost`

## 4. 厳格度モード (Strictness)
- **`permissive`**: 欠損があっても可能な限り合算する。
- **`balanced` (デフォルト)**: 主要コンポーネントが揃えば推定値を算出する。
- **`strict`**: 仕入れ原価、送料、輸入費用、販売手数料のいずれかが欠けた場合に `UNRESOLVED` とする。

## 5. 判定ステータスと信頼度
- **Resolution Status**: `RESOLVED_EXACT`, `RESOLVED_ESTIMATED`, `RESOLVED_PARTIAL`, `FALLBACK_DEFAULT`, `UNRESOLVED`
- **Confidence**: `HIGH` (全主要項目の確度が高い), `MEDIUM`, `LOW` (fallback 依存あり), `NONE`

## 6. 実装構造
- `src/total_cost/models.py`: 出力モデル `TotalCostResult` および集約状態 Enum
- `src/total_cost/resolver.py`: 統合ロジック本体
- `tests/test_total_cost_resolver.py`: 統合テスト

## 7. 注意事項
- **税の扱い**: `collected_tax` は買い手の支払総額には含めるが、セラーの利益ベースの売上からは除外する。
- **説明可能性**: どのコンポーネントがフォールバックされたか、または未解決かを `fallback_components` / `unresolved_components` フィールドで保持する。
