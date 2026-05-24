# Antigravity 実装指示テンプレ

## テンプレ本体

\\\
【対象フェーズ】
Phase X / XXXXX Layer

【今回やること】
- 対象タスクを実装
- 必要なテストを追加
- migration を作成/適用
- CLI/Web/Orchestrator を必要に応じて統合
- task.md / walkthrough.md を更新
- pytest 実行
- git commit / push

【固定ルール】
- seller/environment guard を壊さない
- dry_run / idempotent を維持
- 非スコープは触らない
- 既存フェーズを壊さない
- 重要入力欠損を silent success しない
- 安全制御を bypass しない

【今回の対象ファイル】
- [ファイルA]
- [ファイルB]
- ...

【非スコープ】
- [非対象A]
- [非対象B]
- ...

【完了条件】
- [条件1]
- [条件2]
- [条件3]
- ...

【最終報告フォーマット】
1. 作成/変更ファイル一覧
2. 実装した主要クラス/サービス一覧
3. migration revision ID
4. pytest結果
5. commit message
6. commit hash
7. push成功可否
8. 未解決事項
\\\

## 使用方法

1. このテンプレをコピー
2. 以下を埋める：
   - Phase / Layer
   - 対象ファイル一覧
   - 非スコープ
   - 完了条件（3項目以上）
3. 【固定ルール】と【最終報告フォーマット】は変更しない
4. Antigravity に投げる

## チェックリスト

- [ ] Phase / Layer が明記されている
- [ ] 対象ファイルが3項目以上ある
- [ ] 非スコープが明確に定義されている
- [ ] 完了条件が3項目以上、かつ検証可能である
- [ ] 固定ルールがすべて含まれている

---
*Generated: 2026-05-24 16:30:52*
