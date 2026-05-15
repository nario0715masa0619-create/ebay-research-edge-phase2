# SellingFeeResolver 設計書 v0.1

## 1. 目的
本設計書は、eBay で商品を販売した際に発生する販売関連手数料を自動推定する SellingFeeResolver の仕様を定義する。
本 resolver は、送料、輸入費用、payout fee とは独立したコスト層として動作し、販売時点における eBay 側の手数料コストを説明可能な形で返すことを目的とする。

## 2. 背景
eBay の販売手数料（Final Value Fee 等）は、マーケットプレイス、カテゴリ、価格帯、ストアプラン、出品条件などにより複雑に変動する。これらを独立したコンポーネントとして分解・推定することで、正確な利益予測と説明性を確保する。

## 3. 基本方針
SellingFeeResolver は、利用可能なルールと販売条件に基づいて selling-related fee を推定する。

優先順位:
1. `selling_fee_rule_override`: 個別アカウントや実績ベースの特例ルール
2. `selling_fee_rule_master`: 標準的なマーケットプレイス手数料マスタ
3. `fallback_rule`: 外部から注入される暫定ルール
4. 内部最小 fallback: システム定義の最終救済ルール
5. `unresolved`: 判定不能

## 4. 手数料コンポーネント
- **Final Value Fee (FVF)**: 商品・送料・税の合計に対する変動率手数料
- **Final Value Fee Fixed**: 注文あたりの固定手数料
- **Insertion Fee**: 出品手数料
- **Ad Fee (Promoted Listing)**: 広告プロモーション費用
- **International Fee**: 越境販売による追加手数料
- **Regulatory Operating Fee**: 市場別の規制運用費用
- **Payment Processing Fee**: 決済処理費用

## 5. 厳格度モード (Strictness)
- **`permissive`**: 積極的に内部 fallback を利用し、値を返す。
- **`balanced` (デフォルト)**: マスタ不足時に一部 fallback を許容する。
- **`strict`**: 確実なルールがない場合は `UNRESOLVED` を返し、推測を排除する。

## 6. 実装構造
- `src/selling_fee/models.py`: 出力モデル `SellingFeeResult` および Enums
- `src/selling_fee/resolver.py`: 推定ロジック本体
- `tests/test_selling_fee_resolver.py`: 単体テスト

## 7. 注意事項
- **具体度（Specificity）**: カテゴリ、価格帯、ストアプラン等の条件が多いルールを優先的に採用する。
- **複数適用**: 異なるコンポーネント（FVF + 固定費 + 広告費等）のルールは同時に適用され、合算される。
- **説明可能性**: どのコンポーネントにどのルールが適用されたかを notes に残す。
