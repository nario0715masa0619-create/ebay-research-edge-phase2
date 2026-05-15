# eBay送料自動集計ロジック設計書 v0.1

## 1. 設計目的
本ロジックの目的は、eBay商品1件に対して、利益計算に使える送料関連情報を「説明可能な形」で1つの結果オブジェクトに正規化して返すことです。返却対象は単なる送料金額ではなく、取得元・確定度・税/VAT文脈・返品リスク・輸入費用分離を含む評価済み結果です。

## 2. 責務
- 送料情報の確定・推定・信頼度付け
- search/detail snapshot からの正規化
- shipping options の抽出と選定
- VAT / 税 / import charges / return risk の補完

## 3. 非責務
- 最終利益額の算出
- eBay販売手数料の完全見積もり
- 自動購入 / checkout
- 実際の配送ラベル購入

## 4. 入力
- item_id
- marketplace_id
- delivery_country
- enduser_context または buyer_context
- quantity
- search_snapshot
- detail_snapshot
- fallback_shipping_value

## 5. 出力
- shipping_estimated_total
- shipping_currency
- shipping_source_level
- shipping_cost_type
- shipping_resolution_status
- shipping_confidence
- vat_included_flag
- taxes_included_flag
- import_charges_included_flag
- import_charges_estimated_total
- return_shipping_risk_flag
- quantity_basis
- delivery_context_used
- selected_option_summary
- raw_shipping_options_snapshot
- notes

## 6. 優先順位
1. detail snapshot の配送可能な FIXED 明示送料
2. detail snapshot の配送可能な CALCULATED 送料
3. search snapshot の配送可能な FIXED 明示送料
4. search snapshot の配送可能な CALCULATED 送料
5. fallback shipping
6. unresolved

## 7. 選定ルール
- detail を search より優先
- FIXED を CALCULATED より優先
- 配送可能な option のみ対象
- local pickup only は除外
- 同条件なら最安送料を採用
- shipping と import charges は分離
- 通貨は保持し、自動換算しない

## 8. 状態定義
- resolved_exact
- resolved_estimated
- resolved_partial
- fallback_default
- unresolved

## 9. 信頼度定義
- high
- medium
- low
- none

## 10. 例外ケース
- shippingCost 不在
- local pickup only
- CALCULATED のみ
- 税込みか不明
- import charges 別建て
- 返品送料 seller 負担
- fallback 使用
- unresolved

## 11. 擬似ルール
- detail に有効候補があれば detail で確定
- なければ search を見る
- 有効候補が複数ある場合は最安を採用
- 明示 FIXED があれば exact
- CALCULATED は estimated
- 情報不足なら partial
- fallback を使ったら fallback_default
- どれも無理なら unresolved

## 12. 実装メモ
- 元 snapshot は可能な範囲で保持
- notes に判定理由を残す
- confidence は fallback / context 欠落 / CALCULATED で下げる
- import charges は separate field を使う
