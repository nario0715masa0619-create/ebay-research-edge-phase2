# Notification CLI / Admin Notifications 設計書 v0.1

## 1. 目的
既存の Alert / Notification Layer で管理される通知イベントや履歴を、運用者が CLI から直接操作・確認・診断できるようにする。

## 2. 実装されたコマンド
- `notifications recent`: 直近の通知履歴を表示。
- `notifications failed`: 送信失敗した通知を一覧表示。
- `notifications show`: 特定の通知の詳細を表示（メタデータ含む）。
- `notifications resend`: 失敗またはスキップされた通知の再送。
- `notifications test`: 各チャネルへのテスト通知送信。
- `notifications rules`: 適用されているルールの確認。
- `notifications channels`: 送信チャネルの状態確認。
- `notifications stats`: 通知統計（件数、ステータス比率等）の表示。

## 3. コンポーネント構成
- **NotificationOpsService**: 全コマンドの窓口となるファサード。
- **NotificationHistoryQueryService**: 履歴の検索と整形。
- **NotificationResendService**: イベントの再構築と再送実行。
- **NotificationTestService**: 疎通確認用サービス。
- **NotificationCliMasker**: 出力時の機密情報隠蔽。

## 4. セキュリティ方針
- `access_token`, `secret`, `webhook_url` 等の文字列が含まれる場合は、表示前に `***MASKED***` に置換します。
- `resend` コマンドは `--confirm` または `--dry-run` を必須とし、意図しない実送信を防止します。

## 5. 出力形式
- `--format table`: 人間が見やすいテーブル形式（デフォルト）。
- `--format json`: プログラム処理用の JSON 形式。
- `--format text`: 詳細表示用のテキスト形式。
