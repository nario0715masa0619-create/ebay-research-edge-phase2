# Listing Sync / Recovery Gateway 設計書 v0.1

## 1. 目的
eBay publish 後の内部 DB と eBay 実状態のズレを同期・補正する Listing Sync / Recovery Gateway の設計。
getOffer, getOffers, getInventoryItems を用いた状態照合、差分分類、必要最小限の recovery、DB 補正、evidence / event / jobrun 記録を一貫して提供する。

## 2. ゴール
- 内部 DB の EbayListing と eBay 実状態を再同期できる
- offer_id, listing_id, quantity, price, status の欠損や不整合を補正できる
- publish 済みか不明な中間状態を recovery できる
- orphaned offer / orphaned inventory item を検出できる
- recoverable error と manual review 必須ケースを分類できる

## 3. 主要コンポーネント

### 3.1 状態取得・比較 (`src/listing_sync/`)
- **`EbayStateFetcher`**: 
    - `getOffer` (offer_id 指定)
    - `getOffers` (sku 指定)
    - `getInventoryItem` (sku 指定)
    を組み合わせ、eBay 側の実測値（Truth）を取得する。
- **`StateComparator`**: 
    DB と eBay 実状態を比較し、以下の Drift（乖離）を分類する：
    - `missing_offer_id_in_db`
    - `missing_listing_id_in_db`
    - `price_drift` / `quantity_drift`
    - `listing_status_drift` / `offer_status_drift`
    - `inventory_missing_remote` / `offer_missing_remote`
- **`SyncTargetSelector`**: 
    listed, paused, approved, listing_ready 等のステータスを持つ候補を抽出する。

### 3.2 リカバリ判断・実行
- **`RecoveryDecisionEngine`**: 
    Drift の種類に基づき、`repair_db_ids_only`, `reconcile_remote_from_db`, `mark_review_required` 等の Action を決定する。
- **`OfferRecoveryExecutor` / `InventoryRecoveryExecutor`**: 
    `updateOffer`, `bulkUpdatePriceQuantity`, `withdrawOffer` 等を実行して eBay 側を補正する。

### 3.3 統合・監査
- **`ListingSyncRecoveryGateway`**: 
    同期・リカバリのオーケストレーション。
- **Audit Logging**: 
    `CandidateEvidence` にリクエスト・レスポンス・比較・判断の全過程を記録。
    `MonitoringEvent` に不整合検知と補正結果を記録。
    `JobRun` に全体の統計（synced, repaired, review_required 等）を集計。

## 4. 同期・修復の判断ルール
1. **ID 補正**: eBay 側に有効な Offer が存在するが DB に ID がない場合、DB を補正する（`repair_db_ids_only`）。
2. **価格・在庫不整合**: `allow_recover_inventory` フラグに基づき、DB または Remote どちらを優先するか決定する。
3. **リモート欠損**: eBay 側にアイテムが存在しない場合、不用意に削除せず `review_required` へ振り分ける。
4. **ステータス整合**: Remote が Withdrawn なら DB も Paused/Invalid へ補正する。

## 5. 推奨関数
- `sync_and_recover_listing(candidate_id, run_id, dry_run, ...)`
- `run_listing_sync_recovery_gateway(candidate_ids, limit, dry_run, ...)`

## 6. テストケース
- offer_id あり getOffer 成功で差分なし
- listing_id 欠損を remote から補完
- remote quantity=0 を reconcile
- dry_run で永続更新なし
- JobRun 集計更新
