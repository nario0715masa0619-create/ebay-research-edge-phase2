# ImportChargeResolver 設計書 v0.1

## 1. 目的
本設計書は、eBay 商品の国際取引において発生し得る関税、輸入消費税、VAT、通関関連費、その他 import charges を自動集計する ImportChargeResolver の仕様を定義する。
本 resolver は、既存の ShippingResolver とは独立したコスト層として動作し、総コスト算出および標準スコア計算のための「輸入関連コスト」を返すことを目的とする。

## 2. 背景
eBay の公式ヘルプによれば、国際購入時の import charges には、duty、VAT、tariffs、brokerage fees、handling fees などが含まれ得る。また listing に表示される import charges は見積であり、最終コストは checkout 時に確定する場合がある。
このため、送料だけを集計しても landed cost は完成しない。ShippingResolver とは別に、import charges 専用 resolver を持つ必要がある。

## 3. 基本方針
ImportChargeResolver は「正確な税額計算機」ではなく、eBay API が返す import/tax 情報を正規化し、足りない場合は fallback で暫定推定する説明可能な resolver とする。

優先順位:
1. `getItem` (Detail) API の `shippingOptions.importCharges`
2. `getItem` (Detail) API の `taxes` コンテナ
3. 業務側 fallback rule (暫定マスタ)
4. unresolved (判定不能)

## 4. 判定ステータスと信頼度
- **Source Level**: `detail_import_charges`, `detail_taxes`, `fallback_master`, `unresolved`
- **Resolution Status**: `resolved_exact`, `resolved_estimated`, `resolved_partial`, `fallback_default`, `unresolved`
- **Confidence**: `high` (明示額あり), `medium` (税率等あり), `low` (fallback依存), `none`

## 5. 支払タイミングの管理
eBay の仕様に基づき、以下のフラグを保持する：
- `payable_at_checkout_flag`: チェックアウト時に支払う（eBay Collect and Remit 等）
- `payable_on_delivery_flag`: 配送時に配送業者へ支払う（関税の事後納付等）

## 6. 実装構造
- `src/import_cost/models.py`: 出力モデル `ImportChargeResult` および Enums
- `src/import_cost/resolver.py`: 集計ロジック本体
- `tests/test_import_charge_resolver.py`: 単体テスト

## 7. 注意事項
- **独立性**: 送料 (Shipping Cost) と輸入費用 (Import Charges) は混同せず、別フィールドで保持する。
- **説明可能性**: 総額だけでなく、どの情報を使い、どのような支払条件か、notes や flags に残す。
