# eBay送料自動集計機能 仕様書 v0.1

## 1. 概要
本仕様書は、eBay商品の利益計算に必要な送料関連コストを自動集計する機能の要件を定義する。対象機能は、eBay公式APIから取得できる配送・税・返品関連情報を配送先コンテキスト込みで正規化し、送料額そのものに加えて確定度・信頼度・税文脈を含む「説明可能な送料推定結果」を返す標準モジュールである。

本機能の位置づけは、以下の全体パイプライン内の「送料自動集計」である。

```text
eBay商品探索 → 商品詳細取得 → 送料自動集計 → 総コスト推定 → 利益/ROI/標準スコア算出 → 保存
```

## 2. 目的
本機能の目的は、eBay商品の利益計算に必要な送料関連コストを、商品ページ依存の手作業ではなく、APIおよび取得可能な商品情報から自動で集計・正規化し、下流の利益計算・標準スコア計算に渡せる状態にすることである。

本仕様における「送料」は `shippingCost` 単独を意味しない。以下を含む「送料コストモデル」として扱う。

- 販売時の配送コスト
- 配送条件に由来する不確実性
- 税 / VAT 文脈
- 必要に応じた輸入費用関連情報
- 返品時のコストリスク情報

## 3. スコープ

### 3.1 対象に含むもの
- 商品の配送コスト
- 配送コストの計算方式
- 配送条件のコンテキスト依存性
- VAT込み / 税込みの扱い
- 必要に応じた輸入費用関連情報
- 返品送料負担に関する補助情報
- 送料情報の信頼度・確定度の評価

### 3.2 対象に含まないもの
- 最終利益額の算出
- eBay販売手数料の完全見積もり
- 購入代行やチェックアウト自動化
- 実際の配送ラベル購入や配送手続き
- 倉庫費・梱包資材費・人件費などの社内固定費

## 4. 前提・設計方針

### 4.1 取得元の標準方針
データ取得元は eBay公式API を優先する。

| 優先順位 | 取得元 | 用途 |
|---|---|---|
| 1 | Browse API `search` | 候補一覧の一次評価、概算送料の取得 |
| 2 | Browse API `getItem` | 個別商品の詳細精査、税・返品条件を含む補完 |

商品ページHTMLや画面スクレイピングは、eBayの自動アクセス制限および安定性の観点から標準経路に含めない。

### 4.2 責務
本機能の責務は「送料情報をできるだけ正確かつ説明可能な形で返すこと」である。最終利益判定は責務外とする。

### 4.3 設計原則
- 配送先コンテキスト付き取得を基本とする
- 検索結果より詳細結果を優先する
- フォールバックは例外処理であり、通常系ではない
- 数値だけでなく根拠と信頼度を返す
- 送料結果は永続的真実ではなく、時点付きスナップショットとして扱う

## 5. 入力仕様

### 5.1 入力項目一覧
| 項目名 | 必須 | 説明 |
|---|---:|---|
| `item_id` | Yes | eBay商品ID |
| `marketplace_id` | Yes | マーケットプレイス識別子 |
| `delivery_country` | Yes | 配送先国 |
| `buyer_context` または `enduser_context` | Yes | 配送先文脈。必要に応じて郵便番号や地域情報を含む |
| `quantity` | Yes | 見積もり対象数量 |
| `currency_preference` | No | 表示 / 計算上の希望通貨 |
| `search_snapshot` または `item_detail_snapshot` | Yes | 取得済みのAPIレスポンススナップショット |

### 5.2 配送先コンテキスト
送料やVAT込み価格は配送先依存で変化しうるため、配送先コンテキストは必須思想として扱う。特に `shippingCostType=CALCULATED` の場合、この情報なしでは精度が著しく低下する。

### 5.3 数量
送料見積もりは数量依存の可能性があるため、`quantity` を明示入力とする。

## 6. 取得対象フィールド

### 6.1 Search レベル
| フィールド | 用途 |
|---|---|
| `itemSummaries.price` | 商品価格の把握 |
| `itemSummaries.shippingOptions` | 配送オプションの取得 |
| `itemSummaries.shippingOptions.shippingCost` | 概算送料の取得 |
| `itemSummaries.shippingOptions.shippingCostType` | 固定送料 / 変動送料の判定 |
| `itemSummaries.marketingPrice` | 割引価格文脈の補足 |

### 6.2 getItem レベル
| フィールド | 用途 |
|---|---|
| `price` | 詳細商品価格の取得 |
| `shippingOptions` | 詳細配送オプションの取得 |
| `taxes` | 税情報の補足 |
| `ecoParticipationFee` | 付随費用の補足 |
| `returnTerms.returnShippingCostPayer` | 返品送料リスク判定 |
| `returnTerms.restockingFeePercentage` | 返品時追加コストの補足 |

## 7. 出力仕様
出力は単一数値ではなく、送料推定結果オブジェクトとする。

### 7.1 最低限の出力項目
| 項目名 | 説明 |
|---|---|
| `shipping_estimated_total` | 推定送料合計 |
| `shipping_currency` | 送料通貨 |
| `shipping_source_level` | `search` / `detail` / `fallback` |
| `shipping_cost_type` | 固定 / 変動などの送料種別 |
| `shipping_confidence` | `high` / `medium` / `low` / `none` |
| `shipping_resolution_status` | 解決状態 |
| `vat_included_flag` | VAT込みかどうか |
| `import_charges_included_flag` | 輸入費用込みかどうか |
| `taxes_included_flag` | 税込みかどうか |
| `return_shipping_risk_flag` | 返品送料リスク有無 |
| `quantity_basis` | 見積もり時の数量 |
| `delivery_context_used` | 使用した配送先コンテキスト |
| `raw_shipping_options_snapshot` | 元データのスナップショット |
| `notes` | 補足・注意事項 |

## 8. 状態定義
| 状態 | 定義 |
|---|---|
| `resolved_exact` | 配送先コンテキスト込みで送料取得済み、変動条件が少ない |
| `resolved_estimated` | 送料値は取得済みだが、`CALCULATED` 等により変動余地がある |
| `resolved_partial` | 送料本体はあるが、税・輸入費・地域補正等が一部欠けている |
| `fallback_default` | APIで確定できず、既定送料またはカテゴリ既定値を使用 |
| `unresolved` | 有効な送料を計算できない |

## 9. 信頼度定義
| 信頼度 | 定義 |
|---|---|
| `high` | 詳細API、配送先コンテキスト、送料、通貨、数量条件が明確 |
| `medium` | 送料は取得済みだが、`CALCULATED` や税文脈不足など一部不確実性あり |
| `low` | 既定値フォールバックや国別補正を含む推定 |
| `none` | 実用的な送料推定ができない |

## 10. 税・VAT・輸入費用の扱い
- 商品価格および送料は、リクエスト条件により VAT込みとなる場合があるため、`vat_included_flag` を保持する
- `marketplace_id` や `enduser_context` が不足している場合は、税込み / 税抜きの意味が変わるため、数値だけでなく課税文脈を保持する
- `taxes`、`ecoParticipationFee`、返品送料負担者など、送料リスクに影響する付随情報も標準的に保持する
- 輸入費用が別建ての場合は、純送料と混同せずフラグまたは別項目で扱う

## 11. 例外ケース
| 例外ケース | 取扱方針 |
|---|---|
| `shippingCost` が存在しない | 未設定・取得不能・地域依存未解決を想定。即 `unresolved` にせず、detail再取得やコンテキスト再設定余地を残す |
| `shippingCostType = CALCULATED` | `resolved_exact` ではなく `resolved_estimated` として扱う |
| 税込みか不明 | `vat_included_flag=unknown` とし、信頼度を下げる |
| 通貨が利益計算基準通貨と異なる | 元通貨を保持し、換算は別レイヤーへ委譲可能とする |
| 返品条件が送料リスクに影響 | seller負担時は `return_shipping_risk_flag` を立てる |
| 輸入費用が別建て | `shipping_estimated_total` に含めるか別列に分離するかは後続設計で決定 |

## 12. フォールバック方針
以下の優先順位で送料を解決する。

1. APIで取得できる送料を最優先
2. `detail` を `search` より優先
3. 配送先コンテキスト付き取得を優先
4. 数値が取得できない場合のみ既定送料を使用
5. 既定送料使用時は `shipping_confidence` を下げる
6. `unresolved` は利益計算対象から除外可能とする

フォールバック利用は許容するが、標準値ではなく例外処理と位置付ける。

## 13. 保存仕様
送料自動集計結果は、スプレッドシートまたはDBへ保存可能な形式に標準化する。

### 13.1 最低限保存すべき列
| 列名 | 説明 |
|---|---|
| `shipping_estimated_total` | 推定送料合計 |
| `shipping_currency` | 送料通貨 |
| `shipping_cost_type` | 送料種別 |
| `shipping_resolution_status` | 解決状態 |
| `shipping_confidence` | 信頼度 |
| `vat_included_flag` | VAT込みフラグ |
| `import_charges_included_flag` | 輸入費用込みフラグ |
| `delivery_country` | 配送先国 |
| `quantity_basis` | 数量基準 |
| `shipping_source_level` | 取得元レベル |
| `shipping_notes` | 補足 |

## 14. 非機能要件
- 再取得可能性を前提とした設計とする
- 送料結果は時点付きスナップショットとして扱う
- API制限を考慮し、必要以上の詳細再取得を避ける
- 根拠追跡可能性を確保するため、元データスナップショット保持を推奨する

## 15. 未確定論点
- import charges を shipping に含めるか別列にするか
- 税を shipping cost モデルに含めるか、総コストモデル側で扱うか
- 地域別既定送料の粒度
- `shippingCostType` ごとの補正式
- quantity 複数時の集計ルール
- seller location / item location の影響範囲

## 16. 一文要約
送料自動集計機能は、eBay公式APIから取得できる配送・税・返品関連情報を配送先コンテキスト込みで正規化し、送料額そのものに加えて確定度・信頼度・税文脈を含む「説明可能な送料推定結果」を返す標準モジュールである。

## 17. 参考ソース
- https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
- https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem
- https://developer.ebay.com/api-docs/buy/browse/overview.html
- https://developer.ebay.com/develop/get-started/api-call-limits
- https://www.ebay.com/robots.txt
