# CSV 仕様書

## 基本情報
- ファイル名: listings_sample.csv 
- 文字コード: UTF-8 (BOM なし)
- 必須ヘッダ: sku,title,description,price,quantity,condition,brand,mpn

## 各カラムの詳細
- sku (文字列, 必須): 一意のSKU識別子
- 	itle (文字列, 必須): 最大80文字
- description (文字列, 必須): 最大4000文字
- price (小数, 必須): 0以上の出品価格(USD)
- quantity (整数, 必須): 在庫数
- condition (文字列, 必須): New / Used / Refurbished / For Parts
- rand (文字列, 必須): ブランド名
- mpn (文字列, 必須): 型番（不明時はN/A等）
