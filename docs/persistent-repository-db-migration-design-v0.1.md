# Persistent Repository / DB Migration 設計書 v0.1

## 1. 目的
現在の in-memory Repository 群を SQLAlchemy 2.x ベースの永続 DB (SQLite/PostgreSQL) へ移行し、データの永続性、再実行性、および監査性を確保する。

## 2. 実装済みコンポーネント

### 2.1 データベース基盤
- **Config**: `src/db/config.py` (DATABASE_URL, WAL モード, Foreign Key 等の設定)
- **Engine**: `src/db/engine.py` (SQLAlchemy Engine 生成、SQLite 用 Pragma 設定)
- **Session**: `src/db/session.py` (Session 工場、Scoped Session)
- **Base**: `src/db/base.py` (DeclarativeBase)
- **Models**: `src/db/models.py` (全 6 テーブルの ORM 定義)
- **UnitOfWork**: `src/db/unit_of_work.py` (トランザクション管理用)
- **Bootstrap**: `src/db/bootstrap.py` (DB 初期化、Repository Provider)

### 2.2 永続 Repository
- `PersistentSourceItemRepository`
- `PersistentProductCandidateRepository`
- `PersistentCandidateEvidenceRepository`
- `PersistentEbayListingRepository`
- `PersistentMonitoringEventRepository`
- `PersistentJobRunRepository`

## 3. テーブル定義

| テーブル名 | 用途 | 主要キー / 制約 |
| :--- | :--- | :--- |
| `source_items` | 仕入れ元商品情報 | `source_item_id`, `(platform, url)` unique |
| `product_candidates` | 出品候補 (Research) | `candidate_id`, `sku` unique, `source_item_id` FK |
| `candidate_evidences` | パイプライン証跡 | `evidence_id`, `candidate_id` FK |
| `ebay_listings` | eBay 出品状態 | `sku` unique, `offer_id` unique, `listing_id` unique |
| `monitoring_events` | 監視・改定履歴 | `event_id`, `sku` index |
| `job_runs` | ジョブ実行メトリクス | `run_id` unique |

## 4. 永続化方針
- **JSON 保存**: `JSON` 型（SQLite では文字列、PostgreSQL では JSONB 相当）を使用して、証跡データやメタデータを柔軟に保存。
- **標準化**: `Mapped[]` アノテーションによる SQLAlchemy 2.0 準拠の定義。
- **Idempotency**: `sku` や `source_item_id` による一意性制約を活用。
- **状態保護**: `status` カラムのインデックス化と Repository によるフィルタリング。

## 5. Migration 管理 (Alembic)
- **初期化**: `alembic.ini`, `alembic/env.py` を構成。
- **初期リビジョン**: `alembic/versions/c186701f961f_initial_migration.py` (自動生成済み)。
- **自動アップグレード**: 起動時に Alembic を通じてスキーマを最新化する機能を `bootstrap.py` に実装。

## 6. テスト状況
- **テストファイル**: `tests/test_persistent_repositories.py`
- **内容**: 
    - 各リポジトリの CRUD / Upsert 操作
    - UnitOfWork によるロールバック検証
    - JobRun の進捗追加 (`append_progress`) 検証
- **結果**: 7 件のテストすべて PASS

## 7. PostgreSQL 互換性
- SQLAlchemy 2.0 の抽象化により、`DATABASE_URL` を PostgreSQL (psycopg2) に変更するだけで動作可能。
- `JSON` 型の利用により、PostgreSQL では自動的に `JSONB` への最適化が可能。
- `ON CONFLICT` 相当のロジックを Repository 内の `upsert` に集約。

## 8. 利用方法
```python
from src.db.session import create_session_factory
from src.db.bootstrap import get_repository_provider

session_factory = create_session_factory()
repos = get_repository_provider(session_factory)

# 候補の取得
candidate = repos["candidate"].get_by_sku("SKU-123")
```
