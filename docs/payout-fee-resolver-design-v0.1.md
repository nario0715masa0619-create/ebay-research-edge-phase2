# PayoutFeeResolver 設計書 v0.1

## 1. 目的
本設計書は、eBay 販売後に資金を回収する段階で発生する Payoneer 等の受取・出金・両替関連手数料を自動推定する PayoutFeeResolver の仕様を定義する。
本 resolver は、販売手数料や送料、輸入関連費とは独立したコスト層として動作し、最終的な「実受取額（net payout）」を見積もるための payout-related fee を返すことを目的とする。

## 2. 背景
Payoneer の手数料体系は、受取元、通貨、出金先地域、月間取扱高などによって変動する。固定率での計算は利益予測の誤差を招くため、条件に応じた推定が必要である。

## 3. 基本方針
PayoutFeeResolver は、利用可能なルールと口座条件に基づいて payout-related fee を説明可能に推定する。

優先順位:
1. `payout_rule_override`: 個別アカウント向けの特例ルール
2. `payout_rule_master`: 公式 pricing ベースの標準ルールマスタ
3. `fallback_master`: 最低限のデフォルトルール
4. `unresolved`: 判定不能

## 4. 判定ステータスと信頼度
- **Source Level**: `ACCOUNT_SPECIFIC_RULE`, `STANDARD_PRICING_MASTER`, `FALLBACK_MASTER`, `UNRESOLVED`
- **Resolution Status**: `RESOLVED_EXACT`, `RESOLVED_ESTIMATED`, `RESOLVED_PARTIAL`, `FALLBACK_DEFAULT`, `UNRESOLVED`
- **Confidence**: `HIGH` (個別ルール適用), `MEDIUM` (マスタ合致), `LOW` (fallback), `NONE`

## 5. 手数料コンポーネント
- **Receiving Fee**: プラットフォームからの受取手数料
- **Withdrawal Fee**: 銀行口座への出金手数料
- **Conversion Fee**: 通貨変換コスト
- **Cross-border Fee**: 非ローカル出金等の追加コスト

## 6. 実装構造
- `src/payout_cost/models.py`: 出力モデル `PayoutFeeResult` および Enums
- `src/payout_cost/resolver.py`: 推定ロジック本体
- `tests/test_payout_fee_resolver.py`: 単体テスト

## 7. 注意事項
- **説明可能性**: なぜその手数料になったか、どのルールが適用されたかを notes に残す。
- **FxResolver との連携**: 為替レート自体の取得は FxResolver (将来実装) に委譲し、本 resolver は「手数料率や固定費」の算出に集中する。
