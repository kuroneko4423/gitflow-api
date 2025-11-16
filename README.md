# GitHub API FastAPI Service

GitHubの各種操作をFastAPIで提供するREST APIサービスです。完全日本語対応で、3つの主要なGitHub操作エンドポイントを提供します。

## 📁 プロジェクト構成

```
gitflow-api/
├── main.py              # メインのFastAPIアプリケーション
├── requirements.txt     # Python依存パッケージ
├── .env.example        # 環境変数のテンプレート
├── README.md           # プロジェクトドキュメント（本ファイル）
└── docs/               # 詳細ドキュメント
    ├── api_specification.md   # API仕様書
    ├── architecture.md        # アーキテクチャドキュメント
    ├── deployment_guide.md    # デプロイガイド
    └── system_design.md       # システム設計書
```

## 🌟 特徴

- ✅ **完全日本語対応**: すべてのメッセージ、エラー、レスポンスが日本語
- ✅ **自動生成APIドキュメント**: Swagger UI/ReDocによる対話的なドキュメント
- ✅ **非同期処理**: httpxによる高速な非同期HTTP通信
- ✅ **バリデーション**: Pydanticによる堅牢なデータ検証
- ✅ **環境変数管理**: python-dotenvによる安全な設定管理

## 📁 機能

### 1. POST /create-issue - Issue作成&コメント追加
GitHubのIssueを作成し、自動的に「@claude 実装して」というコメントを追加します。

**必須パラメータ:**
- `repository`: リポジトリ名
- `title`: Issueのタイトル
- `body`: Issueの本文

**オプションパラメータ:**
- `labels`: ラベルの配列
- `assignees`: 担当者のGitHubユーザー名の配列
- `milestone`: マイルストーン番号

### 2. POST /create-pr - Pull Request作成
GitHubのPull Requestを作成します。

**必須パラメータ:**
- `repository`: リポジトリ名

**オプションパラメータ:**
- `branch`: PRの元となるブランチ（未指定時は最新コミットのブランチを自動選択）
- `title`: PRのタイトル
- `body`: PRの説明
- `base`: マージ先ブランチ（デフォルト: main）

### 3. POST /approve-merge-pr - Pull Request承認&マージ
GitHubのPull Requestを承認してマージします。

**必須パラメータ:**
- `repository`: リポジトリ名

**オプションパラメータ:**
- `pr_number`: PR番号（未指定時は最新のオープンPRを自動選択）
- `review_comment`: 承認時のコメント（デフォルト: "LGTM"）
- `merge_method`: マージ方法（merge/squash/rebase、デフォルト: merge）
- `commit_title`: マージコミットのタイトル
- `commit_message`: マージコミットのメッセージ

## 🚀 セットアップ

### 前提条件

- Python 3.11 以上
- pip（Pythonパッケージマネージャー）
- GitHub Personal Access Token

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーして、実際の値を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```env
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_OWNER=your-username-or-org
```

### 3. GitHub Personal Access Tokenの取得

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. 「Generate new token」をクリック
4. 必要な権限を選択:
   - `repo` (Full control of private repositories)
5. トークンを生成してコピー

### 4. アプリケーションの起動

```bash
# 開発モード（ホットリロード有効）
uvicorn main:app --reload

# 本番モード
uvicorn main:app --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下のURLでアクセスできます:
- API: http://localhost:8000
- ドキュメント（Swagger UI）: http://localhost:8000/docs
- 代替ドキュメント（ReDoc）: http://localhost:8000/redoc

## 📖 使用例

### 1. Issue作成

```bash
curl -X POST "http://localhost:8000/create-issue" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "title": "新機能の実装",
    "body": "ユーザー認証機能を実装してください。",
    "labels": ["enhancement", "high-priority"],
    "assignees": ["developer1"]
  }'
```

**レスポンス例:**
```json
{
  "success": true,
  "message": "Issueを作成し、コメントを追加しました",
  "data": {
    "issue": {
      "issue_number": 42,
      "issue_url": "https://github.com/owner/repo/issues/42",
      "title": "新機能の実装",
      "state": "open",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "comment": {
      "comment_id": 123456,
      "comment_url": "https://github.com/owner/repo/issues/42#issuecomment-123456",
      "body": "@claude 実装して",
      "created_at": "2024-01-15T10:30:01Z"
    }
  }
}
```

### 2. Pull Request作成

```bash
# ブランチ指定あり
curl -X POST "http://localhost:8000/create-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "branch": "feature-branch",
    "title": "新機能の追加",
    "body": "この機能を追加しました",
    "base": "main"
  }'

# ブランチ自動選択
curl -X POST "http://localhost:8000/create-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "title": "自動PR作成"
  }'
```

**レスポンス例:**
```json
{
  "success": true,
  "message": "Pull Requestを作成しました",
  "data": {
    "pr_number": 15,
    "pr_url": "https://github.com/owner/repo/pull/15",
    "head_branch": "feature-branch",
    "base_branch": "main",
    "title": "新機能の追加"
  }
}
```

### 3. PR承認&マージ

```bash
# PR番号指定
curl -X POST "http://localhost:8000/approve-merge-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "pr_number": 15,
    "review_comment": "承認します！",
    "merge_method": "squash"
  }'

# 最新PR自動選択
curl -X POST "http://localhost:8000/approve-merge-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo"
  }'
```

**レスポンス例:**
```json
{
  "success": true,
  "message": "Pull Requestを承認してマージしました",
  "data": {
    "pr_number": 15,
    "approval": {
      "review_id": 789012,
      "state": "APPROVED",
      "submitted_at": "2024-01-15T11:00:00Z"
    },
    "merge": {
      "sha": "a1b2c3d4e5f6",
      "merged": true,
      "message": "Pull request successfully merged"
    }
  }
}
```

### 4. ヘルスチェック

```bash
curl http://localhost:8000/
```

**レスポンス例:**
```json
{
  "message": "GitHub APIサービスが稼働中です",
  "version": "1.0.0",
  "endpoints": {
    "POST /create-issue": "GitHubのIssueを作成し、自動的にコメントを追加",
    "POST /create-pr": "Pull Requestを作成",
    "POST /approve-merge-pr": "Pull Requestを承認してマージ"
  },
  "environment": {
    "github_token_set": true,
    "github_owner_set": true,
    "github_owner": "your-username"
  }
}
```

## 📚 API ドキュメント

FastAPIは自動的にインタラクティブなAPIドキュメントを生成します。

- **Swagger UI**: http://localhost:8000/docs
  - APIエンドポイントのテストが可能
  - リクエスト/レスポンスのスキーマを確認可能

- **ReDoc**: http://localhost:8000/redoc
  - より読みやすいドキュメント形式

## 🐳 Docker対応（オプション）

Dockerfileを作成して、コンテナ化することも可能です。

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

ビルド&実行:
```bash
docker build -t github-api-service .
docker run -d -p 8000:8000 --env-file .env github-api-service
```

## 🔒 セキュリティに関する注意事項

1. **トークンの管理**: GitHub Personal Access Tokenは機密情報です。必ず`.env`ファイルで管理し、リポジトリにコミットしないでください（`.gitignore`に追加することを推奨）。

2. **権限の最小化**: トークンには必要最小限の権限のみを付与してください。

3. **アクセス制限**: 本番環境では、適切なファイアウォールやAPIゲートウェイで保護してください。

4. **HTTPS**: 本番環境では必ずHTTPS（リバースプロキシ等）を使用してください。

## 🔧 技術スタック

| カテゴリ | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| Webフレームワーク | FastAPI | 0.104.1 | REST API提供 |
| ASGIサーバー | Uvicorn | 0.24.0 | アプリケーション実行 |
| HTTPクライアント | HTTPX | 0.25.1 | 非同期GitHub API通信 |
| データ検証 | Pydantic | 2.5.0 | リクエスト/レスポンス検証 |
| 環境変数管理 | python-dotenv | 1.0.0 | 環境変数読み込み |

## 📦 主要なソースコード構造

### main.py の構成

```python
# 1. Pydanticモデル（リクエスト/レスポンス定義）
- CreateIssueRequest: Issue作成リクエスト
- CreatePRRequest: PR作成リクエスト
- ApproveMergePRRequest: PR承認&マージリクエスト

# 2. ヘルパー関数
- get_headers(): GitHub API認証ヘッダー生成
- get_owner(): 環境変数からオーナー取得
- find_latest_open_pr(): 最新のオープンPR検索
- find_latest_branch(): 最新コミットのブランチ検索

# 3. エンドポイント
- POST /create-issue: Issue作成&コメント追加
- POST /create-pr: Pull Request作成
- POST /approve-merge-pr: PR承認&マージ
- GET /: ヘルスチェック&API情報
```

## 🆚 Google Apps Script版との比較

| 項目 | Google Apps Script | FastAPI (Python) |
|------|-------------------|------------------|
| デプロイ | Google Apps Script環境 | 任意のサーバー/クラウド |
| 言語 | JavaScript | Python |
| 言語対応 | - | **完全日本語対応** |
| 認証 | スクリプトプロパティ | 環境変数 (.env) |
| ドキュメント | 手動 | **自動生成（Swagger/ReDoc）** |
| テスト | doGet関数 | **インタラクティブUI** |
| 非同期処理 | - | **httpxによる非同期処理** |
| データ検証 | 手動 | **Pydanticによる自動検証** |
| スケーラビリティ | Googleの制限あり | サーバースペック次第 |

## 🐛 トラブルシューティング

### よくある問題

1. **`GITHUB_TOKEN環境変数が設定されていません`エラー**
   - `.env`ファイルが正しく配置されているか確認
   - `GITHUB_TOKEN`の値が正しく設定されているか確認

2. **`Pull Requestの取得に失敗しました`エラー**
   - GitHub Personal Access Tokenに`repo`権限があるか確認
   - リポジトリ名とオーナー名が正しいか確認

3. **ポートがすでに使用されている**
   ```bash
   # 別のポートで起動
   uvicorn main:app --port 8001
   ```

## 📝 エラーメッセージ一覧

すべてのエラーメッセージは日本語で表示されます：

- `GITHUB_TOKEN環境変数が設定されていません`
- `GITHUB_OWNER環境変数が設定されていません`
- `Pull Requestの取得に失敗しました`
- `ブランチの取得に失敗しました`
- `Issueの作成に失敗しました`
- `コメントの追加に失敗しました`
- `リポジトリ内にブランチが見つかりません`
- `Pull Requestの作成に失敗しました`
- `リポジトリ内にオープンなPull Requestが見つかりません`
- `Pull Requestの承認に失敗しました`
- `Pull Requestのマージに失敗しました`

## 📚 参考ドキュメント

詳細なドキュメントは`docs/`ディレクトリにあります：

- **API仕様書** (`docs/api_specification.md`): 各エンドポイントの詳細仕様
- **アーキテクチャ** (`docs/architecture.md`): システムアーキテクチャの詳細
- **デプロイガイド** (`docs/deployment_guide.md`): 本番環境へのデプロイ方法
- **システム設計** (`docs/system_design.md`): システム設計の詳細

## 📝 ライセンス

このコードは自由に使用・改変できます。

## 🤝 サポート

問題が発生した場合は、GitHub Issueを作成してください。

## 🔄 更新履歴

### v1.0.0 (2025-11-16)
- ✅ 完全日本語対応
- ✅ すべてのメッセージとエラーを日本語化
- ✅ FastAPI + Uvicorn による実装
- ✅ 非同期処理対応
- ✅ Pydantic によるデータ検証
- ✅ 自動生成APIドキュメント
