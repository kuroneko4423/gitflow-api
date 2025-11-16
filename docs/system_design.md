# GitHub API Service - システム設計書

## 1. 概要

### 1.1 システム名
GitHub API Service (FastAPI版)

### 1.2 目的
GitHub APIを呼び出すためのREST APIサービスを提供し、以下の操作を自動化する：
- Issue の作成とコメント追加
- Pull Request の作成
- Pull Request の承認とマージ

### 1.3 対象範囲
Google Apps Scriptで実装された既存の機能をPython + FastAPIで再実装し、より柔軟なデプロイとスケーラビリティを実現する。

### 1.4 想定ユーザー
- 開発者
- CI/CDパイプライン
- 自動化ツール
- Webhook連携システム

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────┐
│   クライアント    │ (curl, Postman, CI/CD tools)
└────────┬────────┘
         │ HTTP/HTTPS
         ▼
┌─────────────────────────────┐
│   FastAPI Application       │
│  ┌─────────────────────┐   │
│  │  API Endpoints      │   │
│  │  - /create-issue    │   │
│  │  - /create-pr       │   │
│  │  - /approve-merge-pr│   │
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │  Business Logic     │   │
│  │  - find_latest_pr() │   │
│  │  - find_latest_branch()│
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │  HTTP Client        │   │
│  │  (httpx)            │   │
│  └──────────┬──────────┘   │
└─────────────┼───────────────┘
              │ HTTPS
              ▼
┌─────────────────────────────┐
│   GitHub REST API           │
│   api.github.com            │
└─────────────────────────────┘
```

### 2.2 技術スタック

| レイヤー | 技術 | バージョン | 用途 |
|---------|------|----------|------|
| Webフレームワーク | FastAPI | 0.104.1 | REST API実装 |
| ASGIサーバー | Uvicorn | 0.24.0 | アプリケーションサーバー |
| HTTPクライアント | httpx | 0.25.1 | GitHub API呼び出し |
| バリデーション | Pydantic | 2.5.0 | リクエスト/レスポンス検証 |
| 環境変数管理 | python-dotenv | 1.0.0 | 設定管理 |
| 言語 | Python | 3.9+ | 実装言語 |

### 2.3 レイヤー構成

```
┌────────────────────────────────┐
│  Presentation Layer            │  FastAPI endpoints
│  (main.py - Endpoints)         │  - Request/Response handling
└────────────────┬───────────────┘  - Input validation
                 │
┌────────────────▼───────────────┐
│  Business Logic Layer          │  Core functions
│  (main.py - Helper functions)  │  - Auto-detection logic
└────────────────┬───────────────┘  - Data transformation
                 │
┌────────────────▼───────────────┐
│  Integration Layer             │  GitHub API client
│  (httpx)                       │  - HTTP requests
└────────────────┬───────────────┘  - Error handling
                 │
┌────────────────▼───────────────┐
│  External Service              │  GitHub REST API
│  (api.github.com)              │
└────────────────────────────────┘
```

## 3. データモデル

### 3.1 リクエストモデル

#### CreateIssueRequest
```python
{
  "repository": str,           # 必須
  "title": str,                # 必須
  "body": str,                 # 必須
  "labels": List[str] | None,  # オプション
  "assignees": List[str] | None, # オプション
  "milestone": int | None      # オプション
}
```

#### CreatePRRequest
```python
{
  "repository": str,           # 必須
  "branch": str | None,        # オプション（自動検出可能）
  "title": str | None,         # オプション
  "body": str | None,          # オプション
  "base": str | None           # オプション（デフォルト: "main"）
}
```

#### ApproveMergePRRequest
```python
{
  "repository": str,           # 必須
  "pr_number": int | None,     # オプション（自動検出可能）
  "review_comment": str | None, # オプション（デフォルト: "LGTM"）
  "merge_method": str | None,  # オプション（デフォルト: "merge"）
  "commit_title": str | None,  # オプション
  "commit_message": str | None # オプション
}
```

### 3.2 レスポンスモデル

#### 成功レスポンス（共通構造）
```python
{
  "success": bool,
  "message": str,
  "data": {
    # エンドポイント固有のデータ
  }
}
```

#### エラーレスポンス
```python
{
  "detail": str  # HTTPExceptionから自動生成
}
```

## 4. 機能設計

### 4.1 エンドポイント一覧

| エンドポイント | メソッド | 認証 | 説明 |
|--------------|---------|------|------|
| `/` | GET | 不要 | ヘルスチェック |
| `/create-issue` | POST | 環境変数 | Issue作成 |
| `/create-pr` | POST | 環境変数 | PR作成 |
| `/approve-merge-pr` | POST | 環境変数 | PR承認&マージ |

### 4.2 主要機能詳細

#### 4.2.1 Issue作成機能

**処理フロー:**
```
1. リクエスト受信
2. 入力バリデーション（Pydantic）
3. 環境変数チェック（GITHUB_TOKEN, GITHUB_OWNER）
4. GitHub API呼び出し（Issue作成）
5. コメント追加（"@claude 実装して"）
6. レスポンス返却
```

**GitHub API呼び出し:**
- `POST /repos/{owner}/{repo}/issues` - Issue作成
- `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` - コメント追加

#### 4.2.2 PR作成機能

**処理フロー:**
```
1. リクエスト受信
2. 入力バリデーション
3. 環境変数チェック
4. ブランチ決定（指定 or 自動検出）
5. GitHub API呼び出し（PR作成）
6. レスポンス返却
```

**自動検出ロジック:**
- 全ブランチを取得
- 各ブランチの最新コミット日時を取得
- 最新のコミットを持つブランチを選択

**GitHub API呼び出し:**
- `GET /repos/{owner}/{repo}/branches` - ブランチ一覧取得
- `GET /repos/{owner}/{repo}/commits/{sha}` - コミット詳細取得
- `POST /repos/{owner}/{repo}/pulls` - PR作成

#### 4.2.3 PR承認&マージ機能

**処理フロー:**
```
1. リクエスト受信
2. 入力バリデーション
3. 環境変数チェック
4. PR番号決定（指定 or 自動検出）
5. GitHub API呼び出し（PR承認）
6. GitHub API呼び出し（PRマージ）
7. レスポンス返却
```

**自動検出ロジック:**
- オープン状態のPRを取得（作成日時降順、1件）
- 最新のPR番号を使用

**GitHub API呼び出し:**
- `GET /repos/{owner}/{repo}/pulls?state=open` - PR一覧取得
- `POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews` - PR承認
- `PUT /repos/{owner}/{repo}/pulls/{pr_number}/merge` - PRマージ

## 5. セキュリティ設計

### 5.1 認証・認可

#### 環境変数による認証
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `GITHUB_OWNER`: GitHubオーナー名

#### GitHub API認証
```python
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
```

### 5.2 セキュリティ対策

| 項目 | 対策 |
|------|------|
| トークン管理 | 環境変数で管理、コードに埋め込まない |
| 通信暗号化 | HTTPS使用（本番環境） |
| 入力検証 | Pydanticによる自動バリデーション |
| エラーハンドリング | 詳細情報の漏洩防止 |
| レート制限 | GitHub APIのレート制限に準拠 |
| アクセス制御 | ファイアウォール/APIゲートウェイ推奨 |

### 5.3 推奨権限

GitHub Tokenに必要な権限:
- `repo`: フルアクセス（必須）
  - `repo:status`
  - `repo_deployment`
  - `public_repo`
  - `repo:invite`

## 6. エラーハンドリング

### 6.1 エラー分類

| HTTPステータス | 説明 | 発生条件 |
|---------------|------|---------|
| 400 Bad Request | 不正なリクエスト | 必須パラメータ不足 |
| 404 Not Found | リソース未検出 | PR/ブランチが存在しない |
| 500 Internal Server Error | サーバーエラー | 環境変数未設定、API呼び出し失敗 |

### 6.2 エラーレスポンス例

```json
{
  "detail": "GITHUB_TOKEN environment variable is not set"
}
```

### 6.3 GitHub APIエラー処理

```python
if response.status_code != expected_status:
    raise HTTPException(
        status_code=response.status_code,
        detail=f"Failed to {action}: {response.text}"
    )
```

## 7. パフォーマンス設計

### 7.1 非同期処理

- `httpx.AsyncClient`を使用した非同期HTTP通信
- FastAPIのasync/await対応

### 7.2 レート制限対策

GitHub APIレート制限:
- 認証あり: 5,000リクエスト/時間
- 認証なし: 60リクエスト/時間

対策:
- Personal Access Tokenを使用（認証あり）
- 必要に応じてRetry-Afterヘッダーを確認
- 指数バックオフの実装（将来的な拡張）

### 7.3 レスポンス時間

目標値:
- 単一API呼び出し: < 1秒
- 複数API呼び出し（自動検出時）: < 3秒
- PR承認&マージ: < 2秒

## 8. 運用設計

### 8.1 ログ設計

現在の実装:
- FastAPIの標準ログ出力
- Uvicornのアクセスログ

推奨拡張:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 8.2 監視項目

| 項目 | 説明 | 閾値例 |
|------|------|--------|
| レスポンスタイム | API応答時間 | > 5秒で警告 |
| エラー率 | 5xx エラーの割合 | > 5% で警告 |
| GitHub API制限 | 残りリクエスト数 | < 500 で警告 |
| サーバーリソース | CPU/メモリ使用率 | > 80% で警告 |

### 8.3 バックアップ・復旧

- 環境変数のバックアップ（`.env`ファイル）
- コードのバージョン管理（Git）
- 設定ファイルのバックアップ

## 9. 拡張性

### 9.1 将来的な機能拡張

- 認証機能の追加（API Key、OAuth）
- レート制限の実装
- キャッシング機能
- Webhook受信機能
- バッチ処理機能
- データベース連携

### 9.2 スケーラビリティ

水平スケーリング:
- 複数のUvicornワーカー起動
- ロードバランサーの配置
- コンテナ化（Docker/Kubernetes）

垂直スケーリング:
- サーバースペック向上
- 非同期処理の最適化

## 10. テスト戦略

### 10.1 テストレベル

| レベル | 対象 | ツール候補 |
|--------|------|-----------|
| 単体テスト | 個別関数 | pytest |
| 統合テスト | エンドポイント | pytest + TestClient |
| E2Eテスト | 全体フロー | pytest + httpx |
| 負荷テスト | パフォーマンス | Locust, JMeter |

### 10.2 テストケース例

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_issue():
    response = client.post("/create-issue", json={
        "repository": "test-repo",
        "title": "Test Issue",
        "body": "This is a test"
    })
    assert response.status_code == 201
    assert response.json()["success"] == True
```

## 11. デプロイメント

### 11.1 デプロイ方法

1. **ローカル実行**
   ```bash
   uvicorn main:app --reload
   ```

2. **本番サーバー**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Docker**
   ```bash
   docker run -p 8000:8000 --env-file .env github-api-service
   ```

4. **クラウド**
   - AWS Elastic Beanstalk
   - Google Cloud Run
   - Azure App Service
   - Heroku

### 11.2 環境構成

| 環境 | 説明 | 設定 |
|------|------|------|
| Development | 開発環境 | --reload有効 |
| Staging | ステージング | 本番同等設定 |
| Production | 本番環境 | --workers 4, HTTPS |

## 12. 保守性

### 12.1 コード規約

- PEP 8準拠
- Type Hints使用
- Docstring記述

### 12.2 ドキュメント

- README.md: 使用方法
- API仕様: Swagger UI自動生成
- 設計書: 本ドキュメント

### 12.3 バージョン管理

- Semantic Versioning (SemVer)
- Gitによるバージョン管理
- リリースノートの作成

## 13. 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Pydantic公式ドキュメント](https://docs.pydantic.dev/)
- [httpx公式ドキュメント](https://www.python-httpx.org/)
