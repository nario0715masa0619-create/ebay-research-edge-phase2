# Admin / Ops CLI 設計書 v0.1

## 1. 目的
eBay Research Edge Phase 2 の全レイヤを、運用者が手元から安全に操作・確認・再実行・診断できる管理用 CLI を実装する。

## 2. ゴール
- CLI から各主要ジョブを手動実行できる。
- review_required / failed / drift / blocked の対象を一覧・参照できる。
- scheduler の状態確認・起動・停止・単発実行ができる。
- auth / db / repository / config の診断（doctor）を行える。

## 3. 主要コンポーネント

### 3.1 CLI アプリケーション層
- **`AdminCliApp`**: CLI のメインエントリポイント。引数のパースとコマンドのディスパッチを担当。
- **`CliCommandRegistry`**: コマンド名と実行クラスの紐付けを管理。
- **`CliOutputFormatter`**: Table, JSON, Text 形式での出力制御。

### 3.2 サービス層 (Service Layer)
- **`JobOpsService`**: ジョブの実行と結果の集約。
- **`SchedulerOpsService`**: スケジューラの状態取得と制御。
- **`CandidateOpsService` / `ListingOpsService`**: 各ドメインの状態参照と検索。
- **`DoctorService`**: システム全体のヘルスチェック。

## 4. コマンド体系
- `ops jobs`: ジョブ一覧・詳細・実行
- `ops scheduler`: スケジューラ状態・制御
- `ops candidates`: 出品候補の検索・詳細
- `ops listings`: eBay 出品情報の同期・修復
- `ops review`: 確認待ちキューの表示
- `ops jobruns` / `ops evidence` / `ops events`: ログ・証跡の参照
- `ops doctor` / `ops config`: 診断・設定確認

## 5. 安全性・ポリシー
- **Dry-run**: 書き込み系コマンドはデフォルトで `dry_run=True` または `confirm` フラグを要求。
- **Masking**: トークンやシークレットは非表示。
- **Standard Exit Codes**: 成功(0), 不正な引数(1), 非存在(2), 確認待ち(3) 等の終了コードを返却。

## 6. 技術スタック
- `argparse` (標準ライブラリ) をベースに、将来的に `Typer` や `Click` へ移行可能な疎結合設計を採用。
- `tabulate` または自前の `TableRenderer` によるコンソール出力。
