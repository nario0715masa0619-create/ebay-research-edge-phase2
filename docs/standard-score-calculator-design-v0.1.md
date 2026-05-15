# StandardScoreCalculator 設計書 v0.1

## 1. 目的
`TotalCostResolver` の出力をもとに、候補商品の **総合評価スコア** を算出し、利益額だけでなく、利益率・ROI・推定精度・fallback依存度・未解決要素・リスク要素を加味して、比較可能な形でランキングできるようにする。

## 2. スコアリングの基本方針
- **金額系指標** (Profit, Margin, ROI) と **品質系指標** (Confidence, Stability, Quality) を分離して評価。
- スコアは **0〜100** の範囲で算出し、A〜Eの **Grade** を付与する。
- **Scoring Profile** により、利益重視や安定性重視など評価の重み付けを切り替え可能。

## 3. 指標と重み (Balanced Profile)
- `profit_score`: 30% (利益額の大きさ)
- `margin_score`: 20% (利益率)
- `roi_score`: 15% (ROI)
- `confidence_score`: 15% (Resolver全体の信頼度)
- `stability_score`: 10% (欠落・推測項目の少なさ)
- `resolution_quality_score`: 10% (解決ステータスの質)

## 4. ペナルティとリスク評価
- **Stability Penalty**: 未解決項目 (-35), 部分解決 (-15), フォールバック (-10) により減点。
- **Risk Penalty**: 複数フォールバックや赤字リスク、未解決コンポーネントがある場合に最終スコアから減算。

## 5. グレード定義
- `A`: 85〜100 (極めて優秀)
- `B`: 70〜84.99 (優秀)
- `C`: 55〜69.99 (標準)
- `D`: 40〜54.99 (注意が必要)
- `E`: 0〜39.99 (非推奨)

## 6. 実装構造
- `src/score/models.py`: 出力モデル `StandardScoreResult` および関連 Enum
- `src/score/calculator.py`: スコアリングロジック本体
- `tests/test_standard_score_calculator.py`: 単体テスト

## 7. 注意事項
- **非再計算**: 本レイヤーは利益計算を再実装せず、`TotalCostResult` の数値を信頼して評価のみを行う。
- **通貨単位**: v0.1 では単一通貨（USD等）での比較を前提とする。
