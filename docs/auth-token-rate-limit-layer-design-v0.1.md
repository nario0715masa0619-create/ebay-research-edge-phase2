# Auth / Token / Rate Limit Layer 設計書 v0.1

## 1. 目的
eBay API を利用する全レイヤに対して、認証・トークン管理・レート制御・リトライ制御を横断的に提供する共通基盤を構築する。

## 2. 実装済みコンポーネント

### 2.1 認証・トークン管理 (`src/auth/`)
- **`AuthConfig`**: Pydantic による環境変数ベースの設定管理。
- **`TokenInfo`**: トークン、有効期限、スコープ、対象アカウント情報を保持するモデル。
- **`EbayTokenService`**: 
    - **App Access Token**: Client Credentials Grant による発行。
    - **User Access Token**: Refresh Token を用いた自動更新。
    - **Caching**: `InMemoryTokenCache` による有効期間内のトークン再利用。
- **`OAuthScopeRegistry`**: API オペレーション（例: `inventory.create_offer`）と必要な eBay スコープの対応付けを管理。

### 2.2 耐障害性・流量制御
- **`RateLimiter`**: Token Bucket アルゴリズムによるリクエスト流量制御（バースト対応）。
- **`RetryBackoffPolicy`**: 指数バックオフ（Exponential Backoff）とジッターを用いたリトライ制御。
- **`AuthErrorClassifier`**: HTTP ステータスコードに基づき、エラーを `auth_retryable`, `rate_limit_retryable`, `fatal` 等に分類。

### 2.3 API Client 統合 (`src/ebay/`)
- **`EbayBaseApiClient`**: 
    - `execute_with_auth` メソッドを提供。
    - スコープ解決 -> レート制限確認 -> トークン解決 -> HTTP 実行 -> エラー分類 & リトライ の一連のフローをカプセル化。
- **`EbayInventoryApiClient`**: 
    - BaseClient を継承し、各 API エンドポイントを `execute_with_auth` でラップ。

## 3. セキュリティ方針
- **機密情報の非保存**: `access_token` や `refresh_token` の生値は `CandidateEvidence` や `JobRun` 等のログ/永続化対象には含めない。
- **マスク処理**: ログ出力時には認証情報を適切に隠蔽。

## 4. 利用方法

```python
from src.auth.bootstrap import bootstrap_auth_layer
from src.ebay.api_client import EbayInventoryApiClient

# 1. Auth レイヤの初期化
auth_components = bootstrap_auth_layer()

# 2. Client の生成
client = EbayInventoryApiClient(auth_components)

# 3. 実行（Auth/RateLimit が自動適用される）
res = client.publish_offer("OFFER-123")
```

## 5. テスト状況
- `test_auth_token_service.py`: トークン発行・更新・キャッシュの検証。
- `test_rate_limit_layer.py`: スロットリングとバースト制御の検証。
- `test_auth_integration_with_api_client.py`: 401 エラー時の自動リフレッシュとリトライ、Authorization ヘッダ付与の検証。
- **結果**: 全 10 テスト PASS。

## 6. 今後の拡張性
- **PersistentTokenStore**: トークンメタデータの DB 保存。
- **Analytics API 連携**: `getRateLimits` を用いた動的なレート制限同期。
- **複数アカウント対応**: `seller_account_id` ごとのトークンキャッシュ分離。
