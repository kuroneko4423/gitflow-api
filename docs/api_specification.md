# GitHub API Service - API仕様書

## バージョン情報
- **APIバージョン**: 1.0.0
- **作成日**: 2024-01-15
- **更新日**: 2024-01-15

## 目次
1. [概要](#概要)
2. [共通仕様](#共通仕様)
3. [エンドポイント詳細](#エンドポイント詳細)
4. [エラーコード](#エラーコード)
5. [使用例](#使用例)

---

## 概要

### ベースURL
```
http://localhost:8000
```

本番環境では適切なドメインとHTTPSを使用してください。

### 認証方式
環境変数による認証:
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `GITHUB_OWNER`: GitHubオーナー名（ユーザー名または組織名）

### コンテンツタイプ
- リクエスト: `application/json`
- レスポンス: `application/json`

---

## 共通仕様

### リクエストヘッダー

| ヘッダー名 | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| Content-Type | はい | コンテンツタイプ | application/json |

### レスポンス形式

#### 成功レスポンス
```json
{
  "success": true,
  "message": "操作の説明",
  "data": {
    // エンドポイント固有のデータ
  }
}
```

#### エラーレスポンス
```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

| コード | 説明 | 使用場面 |
|--------|------|----------|
| 200 | OK | 正常処理（GET, PUT） |
| 201 | Created | リソース作成成功 |
| 400 | Bad Request | リクエストパラメータエラー |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバーエラー |

---

## エンドポイント詳細

### 1. ヘルスチェック

#### エンドポイント
```
GET /
```

#### 説明
APIサーバーの稼働状態と設定情報を確認します。

#### リクエスト
パラメータなし

#### レスポンス

**ステータスコード**: `200 OK`

```json
{
  "message": "GitHub API Service is running",
  "version": "1.0.0",
  "endpoints": {
    "POST /create-issue": "Create a GitHub issue with automatic comment",
    "POST /create-pr": "Create a Pull Request",
    "POST /approve-merge-pr": "Approve and merge a Pull Request"
  },
  "environment": {
    "github_token_set": true,
    "github_owner_set": true,
    "github_owner": "your-username"
  }
}
```

#### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| message | string | サービス稼働メッセージ |
| version | string | APIバージョン |
| endpoints | object | 利用可能なエンドポイント一覧 |
| environment.github_token_set | boolean | GitHub Tokenが設定されているか |
| environment.github_owner_set | boolean | GitHub Ownerが設定されているか |
| environment.github_owner | string | 設定されているGitHub Owner名 |

---

### 2. Issue作成

#### エンドポイント
```
POST /create-issue
```

#### 説明
GitHub Issueを作成し、自動的に「@claude 実装して」というコメントを追加します。

#### リクエストボディ

```json
{
  "repository": "my-repo",
  "title": "新機能の実装",
  "body": "ユーザー認証機能を実装してください。",
  "labels": ["enhancement", "high-priority"],
  "assignees": ["developer1", "developer2"],
  "milestone": 1
}
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|-----|
| repository | string | ✓ | リポジトリ名 | "my-repo" |
| title | string | ✓ | Issueのタイトル | "新機能の実装" |
| body | string | ✓ | Issueの本文 | "詳細な説明..." |
| labels | array[string] | - | ラベルのリスト | ["bug", "urgent"] |
| assignees | array[string] | - | 担当者のユーザー名リスト | ["user1"] |
| milestone | integer | - | マイルストーン番号 | 1 |

#### レスポンス

**ステータスコード**: `201 Created`

```json
{
  "success": true,
  "message": "Issue created and comment added successfully",
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

#### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| data.issue.issue_number | integer | 作成されたIssue番号 |
| data.issue.issue_url | string | IssueのURL |
| data.issue.title | string | Issueのタイトル |
| data.issue.state | string | Issueの状態（"open", "closed"） |
| data.issue.created_at | string | 作成日時（ISO 8601形式） |
| data.comment.comment_id | integer | コメントID |
| data.comment.comment_url | string | コメントのURL |
| data.comment.body | string | コメント内容 |
| data.comment.created_at | string | コメント作成日時 |

#### エラーレスポンス

**ステータスコード**: `400 Bad Request`
```json
{
  "detail": "repository parameter is required"
}
```

**ステータスコード**: `500 Internal Server Error`
```json
{
  "detail": "GITHUB_TOKEN environment variable is not set"
}
```

---

### 3. Pull Request作成

#### エンドポイント
```
POST /create-pr
```

#### 説明
GitHub Pull Requestを作成します。ブランチが指定されない場合、最新のコミットを持つブランチが自動選択されます。

#### リクエストボディ

```json
{
  "repository": "my-repo",
  "branch": "feature-branch",
  "title": "新機能の追加",
  "body": "この機能を追加しました",
  "base": "main"
}
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | デフォルト | 例 |
|-----------|-----|------|------|-----------|-----|
| repository | string | ✓ | リポジトリ名 | - | "my-repo" |
| branch | string | - | PRの元となるブランチ | 最新ブランチ | "feature-branch" |
| title | string | - | PRのタイトル | "PR from {branch}" | "新機能の追加" |
| body | string | - | PRの説明 | "" | "詳細な説明..." |
| base | string | - | マージ先のブランチ | "main" | "develop" |

#### レスポンス

**ステータスコード**: `200 OK`

```json
{
  "success": true,
  "message": "Pull Request created successfully",
  "data": {
    "pr_number": 15,
    "pr_url": "https://github.com/owner/repo/pull/15",
    "head_branch": "feature-branch",
    "base_branch": "main",
    "title": "新機能の追加"
  }
}
```

#### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| data.pr_number | integer | 作成されたPR番号 |
| data.pr_url | string | PRのURL |
| data.head_branch | string | マージ元のブランチ |
| data.base_branch | string | マージ先のブランチ |
| data.title | string | PRのタイトル |

#### ブランチ自動選択の動作

1. リポジトリの全ブランチを取得
2. 各ブランチの最新コミット日時を取得
3. 最新のコミットを持つブランチを選択

#### エラーレスポンス

**ステータスコード**: `404 Not Found`
```json
{
  "detail": "No branches found in the repository"
}
```

**ステータスコード**: `500 Internal Server Error`
```json
{
  "detail": "Failed to create PR: {詳細メッセージ}"
}
```

---

### 4. Pull Request承認&マージ

#### エンドポイント
```
POST /approve-merge-pr
```

#### 説明
GitHub Pull Requestを承認し、マージします。PR番号が指定されない場合、最新のオープンPRが自動選択されます。

#### リクエストボディ

```json
{
  "repository": "my-repo",
  "pr_number": 15,
  "review_comment": "承認します！",
  "merge_method": "squash",
  "commit_title": "feat: 新機能の追加",
  "commit_message": "詳細なコミットメッセージ"
}
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | デフォルト | 例 |
|-----------|-----|------|------|-----------|-----|
| repository | string | ✓ | リポジトリ名 | - | "my-repo" |
| pr_number | integer | - | PR番号 | 最新オープンPR | 15 |
| review_comment | string | - | 承認コメント | "LGTM" | "承認します！" |
| merge_method | string | - | マージ方法 | "merge" | "squash", "rebase" |
| commit_title | string | - | コミットタイトル | GitHub自動生成 | "feat: 新機能" |
| commit_message | string | - | コミットメッセージ | GitHub自動生成 | "詳細な説明" |

#### マージ方法の種類

| merge_method | 説明 |
|-------------|------|
| merge | 標準的なマージコミットを作成 |
| squash | 全てのコミットを1つにまとめる |
| rebase | リベースしてマージ |

#### レスポンス

**ステータスコード**: `200 OK`

```json
{
  "success": true,
  "message": "PR approved and merged successfully",
  "data": {
    "pr_number": 15,
    "approval": {
      "review_id": 789012,
      "state": "APPROVED",
      "submitted_at": "2024-01-15T11:00:00Z"
    },
    "merge": {
      "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
      "merged": true,
      "message": "Pull request successfully merged"
    }
  }
}
```

#### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| data.pr_number | integer | 処理されたPR番号 |
| data.approval.review_id | integer | レビューID |
| data.approval.state | string | レビュー状態（"APPROVED"） |
| data.approval.submitted_at | string | レビュー送信日時 |
| data.merge.sha | string | マージコミットのSHA |
| data.merge.merged | boolean | マージ成功フラグ |
| data.merge.message | string | マージ結果メッセージ |

#### PR自動選択の動作

1. オープン状態のPRを取得（作成日時降順）
2. 最新のPR（1件目）を選択

#### エラーレスポンス

**ステータスコード**: `404 Not Found`
```json
{
  "detail": "No open pull requests found in the repository"
}
```

**ステータスコード**: `500 Internal Server Error`
```json
{
  "detail": "Failed to approve PR: {詳細メッセージ}"
}
```

---

## エラーコード

### エラー一覧

| HTTPステータス | detail内容 | 原因 | 対処方法 |
|---------------|-----------|------|----------|
| 400 | "repository parameter is required" | リポジトリ名が未指定 | リクエストにrepositoryを含める |
| 400 | "title parameter is required" | タイトルが未指定 | リクエストにtitleを含める |
| 400 | "body parameter is required" | 本文が未指定 | リクエストにbodyを含める |
| 404 | "No branches found in the repository" | ブランチが存在しない | リポジトリにブランチを作成 |
| 404 | "No open pull requests found in the repository" | オープンPRが存在しない | PRを作成するか、pr_numberを指定 |
| 500 | "GITHUB_TOKEN environment variable is not set" | 環境変数未設定 | GITHUB_TOKENを設定 |
| 500 | "GITHUB_OWNER environment variable is not set" | 環境変数未設定 | GITHUB_OWNERを設定 |
| 500 | "Failed to create issue: {詳細}" | GitHub API呼び出し失敗 | GitHub APIのエラーメッセージを確認 |
| 500 | "Failed to create PR: {詳細}" | GitHub API呼び出し失敗 | ブランチ名やリポジトリ名を確認 |
| 500 | "Failed to approve PR: {詳細}" | GitHub API呼び出し失敗 | PR番号やトークン権限を確認 |
| 500 | "Failed to merge PR: {詳細}" | GitHub API呼び出し失敗 | PRの状態やコンフリクトを確認 |

### エラーハンドリングのベストプラクティス

1. **レスポンスのステータスコードを確認**
   ```python
   if response.status_code != 201:
       print(f"Error: {response.json()['detail']}")
   ```

2. **詳細なエラーメッセージを活用**
   - エラーメッセージにはGitHub APIからの詳細情報が含まれます

3. **リトライロジックの実装**
   - 一時的なネットワークエラーに対応
   - 指数バックオフを推奨

---

## 使用例

### cURLでの使用例

#### 1. ヘルスチェック
```bash
curl http://localhost:8000/
```

#### 2. Issue作成
```bash
curl -X POST "http://localhost:8000/create-issue" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "title": "バグ修正",
    "body": "ログイン時にエラーが発生します。",
    "labels": ["bug", "high-priority"]
  }'
```

#### 3. PR作成（ブランチ自動選択）
```bash
curl -X POST "http://localhost:8000/create-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "title": "自動PR作成"
  }'
```

#### 4. PR作成（ブランチ指定）
```bash
curl -X POST "http://localhost:8000/create-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "branch": "feature-branch",
    "title": "新機能の追加",
    "body": "この機能を追加しました",
    "base": "main"
  }'
```

#### 5. PR承認&マージ（自動選択）
```bash
curl -X POST "http://localhost:8000/approve-merge-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo"
  }'
```

#### 6. PR承認&マージ（詳細指定）
```bash
curl -X POST "http://localhost:8000/approve-merge-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-repo",
    "pr_number": 15,
    "review_comment": "素晴らしい実装です！",
    "merge_method": "squash",
    "commit_title": "feat: ユーザー認証機能を追加"
  }'
```

### Pythonでの使用例

```python
import httpx

BASE_URL = "http://localhost:8000"

# Issue作成
async def create_issue():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/create-issue",
            json={
                "repository": "my-repo",
                "title": "新しいIssue",
                "body": "詳細な説明"
            }
        )
        return response.json()

# PR作成
async def create_pr():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/create-pr",
            json={
                "repository": "my-repo",
                "branch": "feature-branch",
                "title": "新機能"
            }
        )
        return response.json()

# PR承認&マージ
async def approve_merge_pr():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/approve-merge-pr",
            json={
                "repository": "my-repo",
                "pr_number": 15
            }
        )
        return response.json()
```

### JavaScriptでの使用例

```javascript
const BASE_URL = 'http://localhost:8000';

// Issue作成
async function createIssue() {
  const response = await fetch(`${BASE_URL}/create-issue`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      repository: 'my-repo',
      title: '新しいIssue',
      body: '詳細な説明'
    })
  });
  return await response.json();
}

// PR作成
async function createPR() {
  const response = await fetch(`${BASE_URL}/create-pr`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      repository: 'my-repo',
      branch: 'feature-branch',
      title: '新機能'
    })
  });
  return await response.json();
}

// PR承認&マージ
async function approveMergePR() {
  const response = await fetch(`${BASE_URL}/approve-merge-pr`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      repository: 'my-repo',
      pr_number: 15
    })
  });
  return await response.json();
}
```

---

## 付録

### A. レート制限

GitHub APIのレート制限:
- 認証あり: 5,000リクエスト/時間
- 認証なし: 60リクエスト/時間

本APIは認証済みリクエストを使用するため、5,000リクエスト/時間の制限が適用されます。

### B. タイムゾーン

すべての日時フィールドはUTC（ISO 8601形式）で返されます。
例: `"2024-01-15T10:30:00Z"`

### C. バージョニング

本APIはSemantic Versioning (SemVer) に従います。
- メジャーバージョン: 互換性のない変更
- マイナーバージョン: 後方互換性のある機能追加
- パッチバージョン: 後方互換性のあるバグ修正

### D. サポート

- GitHub Issues: https://github.com/your-org/your-repo/issues
- ドキュメント: http://localhost:8000/docs
