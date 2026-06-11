# トラブルシューティング詳細ガイド
目次
1. 環境・認証
2. CSV 関連
3. 画像関連
4. Dry-Run
5. Live 実行

## 1. 環境・認証
**Q: .env ファイルが見つからない**
A: ルートディレクトリに .env を作成し EBAY_SANDBOX_CLIENT_ID などを設定してください。

## 2. CSV 関連
**Q: CSV Error: Missing required column 'title'**
A: CSV の先頭ヘッダ行が sku,title,description,price,quantity,condition,brand,mpn になっているか確認してください。

**Q: Duplicate SKU found**
A: CSV内で同じSKUが重複しています。統合・削除してください。

## 3. 画像関連
**Q: Image directory not found: data/images/SKU0099/**
A: 指定したSKUフォルダがありません。作成するかCSVから該当行を削除してください。

**Q: Invalid image file (corrupted)**
A: 画像ファイルが破損しています。別の画像に差し替えてください。

## 4. Live 実行
**Q: eBay API error 21919 (Invalid category)**
A: ペイロードで設定している category_id が現在のeBayで無効です。
