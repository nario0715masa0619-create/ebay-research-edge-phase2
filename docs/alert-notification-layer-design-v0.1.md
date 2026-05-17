# Alert / Notification Layer 設計書 v0.1

## 1. 目的
システム各レイヤで発生する重要イベントを運用者へ通知し、異常検知の即時性と運用負荷の軽減を実現する。

## 2. コア概念
- **`NotificationEvent`**: 発生した事象の正規化データ。
- **`NotificationRule`**: どのイベントを、どの優先度で、どのチャネルに通知するかのルール。
- **`NotificationDispatcher`**: ルールに基づき、実際のチャネル（Slack, Email等）へ配信する。
- **`Deduper / Cooldown`**: 同一または同種の通知の連投を抑止する。

## 3. 主要コンポーネント
- **`NotificationRuleEngine`**: イベントに適合するルールを解決。
- **`PersistentNotificationHistoryRepository`**: 通知結果の永続化。
- **`Notifiers`**: Console, Slack, Email, Webhook への具体的送信処理。

## 4. 通知フロー
1. 各レイヤ（Orchestrator, Auth 等）でイベントが発生。
2. `NotificationService.emit(event)` を呼び出し。
3. `RuleEngine` が重要度・チャネルを決定。
4. `Deduper / Cooldown` が重複を確認。
5. `Dispatcher` が各 `Notifier` を呼び出し。
6. 結果を `NotificationHistory` に保存。

## 5. 安全性
- **Masking**: シークレットやトークンは通知本文に含めない。
- **Non-blocking**: 通知の失敗は主業務のロールバックを引き起こさない。
