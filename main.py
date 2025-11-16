"""
GitHub API FastAPI アプリケーション

このFastAPIアプリケーションは、Google Apps Scriptの機能と同等の3つのエンドポイントを提供します:
1. POST /create-issue - GitHubのIssueを作成してコメントを追加
2. POST /create-pr - Pull Requestを作成
3. POST /approve-merge-pr - Pull Requestを承認してマージ

必要な環境変数:
- GITHUB_TOKEN: GitHub Personal Access Token
- GITHUB_OWNER: GitHubオーナー名（ユーザー名または組織名）
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
import os
from datetime import datetime

app = FastAPI(
    title="GitHub API サービス",
    description="GitHub操作（Issue作成、PR作成、PRマージ）のためのFastAPIサービス",
    version="1.0.0"
)

# 環境変数
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_API_BASE = "https://api.github.com"


# リクエスト/レスポンス用のPydanticモデル
class CreateIssueRequest(BaseModel):
    repository: str = Field(..., description="リポジトリ名")
    title: str = Field(..., description="Issueのタイトル")
    body: str = Field(..., description="Issueの本文/説明")
    labels: Optional[List[str]] = Field(default=None, description="ラベルのリスト")
    assignees: Optional[List[str]] = Field(default=None, description="担当者のユーザー名のリスト")
    milestone: Optional[int] = Field(default=None, description="マイルストーン番号")


class CreatePRRequest(BaseModel):
    repository: str = Field(..., description="リポジトリ名")
    branch: Optional[str] = Field(default=None, description="ヘッドブランチ（未指定時は自動検出）")
    title: Optional[str] = Field(default=None, description="PRのタイトル")
    body: Optional[str] = Field(default="", description="PRの説明")
    base: Optional[str] = Field(default="main", description="マージ先のベースブランチ")


class ApproveMergePRRequest(BaseModel):
    repository: str = Field(..., description="リポジトリ名")
    pr_number: Optional[int] = Field(default=None, description="PR番号（未指定時は最新を自動検出）")
    review_comment: Optional[str] = Field(default="LGTM", description="レビューコメント")
    merge_method: Optional[str] = Field(default="merge", description="マージ方法: merge、squash、rebase")
    commit_title: Optional[str] = Field(default=None, description="マージ時のコミットタイトル")
    commit_message: Optional[str] = Field(default=None, description="マージ時のコミットメッセージ")


# ヘルパー関数
def get_headers():
    """認証付きのGitHub APIヘッダーを取得"""
    if not GITHUB_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GITHUB_TOKEN環境変数が設定されていません"
        )
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }


def get_owner():
    """環境変数からGitHubオーナーを取得"""
    if not GITHUB_OWNER:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GITHUB_OWNER環境変数が設定されていません"
        )
    return GITHUB_OWNER


async def find_latest_open_pr(repository: str) -> Optional[int]:
    """リポジトリ内の最新のオープンなPull Requestを検索"""
    owner = get_owner()
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repository}/pulls"
    params = {
        "state": "open",
        "sort": "created",
        "direction": "desc",
        "per_page": 1
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=get_headers(), params=params)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Pull Requestの取得に失敗しました: {response.text}"
            )

        pull_requests = response.json()
        if not pull_requests:
            return None

        return pull_requests[0]["number"]


async def find_latest_branch(repository: str) -> Optional[str]:
    """最新のコミットを持つブランチを検索"""
    owner = get_owner()
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repository}/branches"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=get_headers())

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ブランチの取得に失敗しました: {response.text}"
            )

        branches = response.json()
        if not branches:
            return None

        # 各ブランチのコミット情報を取得し、最新のものを見つける
        latest_branch = None
        latest_date = None

        for branch in branches:
            commit_url = f"{GITHUB_API_BASE}/repos/{owner}/{repository}/commits/{branch['commit']['sha']}"
            commit_response = await client.get(commit_url, headers=get_headers())

            if commit_response.status_code == 200:
                commit_data = commit_response.json()
                commit_date = datetime.fromisoformat(
                    commit_data["commit"]["committer"]["date"].replace("Z", "+00:00")
                )

                if latest_date is None or commit_date > latest_date:
                    latest_date = commit_date
                    latest_branch = branch["name"]

        return latest_branch


# エンドポイント1: Issue作成
@app.post("/create-issue", status_code=status.HTTP_201_CREATED)
async def create_issue(request: CreateIssueRequest):
    """
    GitHubのIssueを作成し、自動的に「@claude 実装して」のコメントを追加
    """
    owner = get_owner()
    url = f"{GITHUB_API_BASE}/repos/{owner}/{request.repository}/issues"

    # Issueペイロードを準備
    payload = {
        "title": request.title,
        "body": request.body
    }

    if request.labels:
        payload["labels"] = request.labels

    if request.assignees:
        payload["assignees"] = request.assignees

    if request.milestone:
        payload["milestone"] = request.milestone

    async with httpx.AsyncClient() as client:
        # Issueを作成
        response = await client.post(url, headers=get_headers(), json=payload)

        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Issueの作成に失敗しました: {response.text}"
            )

        issue_data = response.json()
        issue_number = issue_data["number"]

        # Issueにコメントを追加
        comment_url = f"{GITHUB_API_BASE}/repos/{owner}/{request.repository}/issues/{issue_number}/comments"
        comment_payload = {"body": "@claude 実装して"}

        comment_response = await client.post(comment_url, headers=get_headers(), json=comment_payload)

        if comment_response.status_code != 201:
            raise HTTPException(
                status_code=comment_response.status_code,
                detail=f"コメントの追加に失敗しました: {comment_response.text}"
            )

        comment_data = comment_response.json()

        return {
            "success": True,
            "message": "Issueを作成し、コメントを追加しました",
            "data": {
                "issue": {
                    "issue_number": issue_data["number"],
                    "issue_url": issue_data["html_url"],
                    "title": issue_data["title"],
                    "state": issue_data["state"],
                    "created_at": issue_data["created_at"]
                },
                "comment": {
                    "comment_id": comment_data["id"],
                    "comment_url": comment_data["html_url"],
                    "body": comment_data["body"],
                    "created_at": comment_data["created_at"]
                }
            }
        }


# エンドポイント2: Pull Request作成
@app.post("/create-pr", status_code=status.HTTP_200_OK)
async def create_pull_request(request: CreatePRRequest):
    """
    GitHubのPull Requestを作成
    ブランチが指定されていない場合、最新のコミットを持つブランチを自動選択
    """
    owner = get_owner()

    # 対象ブランチを決定
    target_branch = request.branch
    if not target_branch:
        target_branch = await find_latest_branch(request.repository)
        if not target_branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="リポジトリ内にブランチが見つかりません"
            )

    # PRペイロードを準備
    pr_title = request.title or f"PR from {target_branch}"
    url = f"{GITHUB_API_BASE}/repos/{owner}/{request.repository}/pulls"
    payload = {
        "title": pr_title,
        "body": request.body,
        "head": target_branch,
        "base": request.base
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_headers(), json=payload)

        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Pull Requestの作成に失敗しました: {response.text}"
            )

        pr_data = response.json()

        return {
            "success": True,
            "message": "Pull Requestを作成しました",
            "data": {
                "pr_number": pr_data["number"],
                "pr_url": pr_data["html_url"],
                "head_branch": target_branch,
                "base_branch": request.base,
                "title": pr_data["title"]
            }
        }


# エンドポイント3: Pull Request承認とマージ
@app.post("/approve-merge-pr", status_code=status.HTTP_200_OK)
async def approve_and_merge_pr(request: ApproveMergePRRequest):
    """
    GitHubのPull Requestを承認してマージ
    PR番号が指定されていない場合、最新のオープンなPRを自動選択
    """
    owner = get_owner()

    # 対象PR番号を決定
    target_pr_number = request.pr_number
    if not target_pr_number:
        target_pr_number = await find_latest_open_pr(request.repository)
        if not target_pr_number:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="リポジトリ内にオープンなPull Requestが見つかりません"
            )

    async with httpx.AsyncClient() as client:
        # PRを承認
        review_url = f"{GITHUB_API_BASE}/repos/{owner}/{request.repository}/pulls/{target_pr_number}/reviews"
        review_payload = {
            "event": "APPROVE",
            "body": request.review_comment
        }

        review_response = await client.post(review_url, headers=get_headers(), json=review_payload)

        if review_response.status_code != 200:
            raise HTTPException(
                status_code=review_response.status_code,
                detail=f"Pull Requestの承認に失敗しました: {review_response.text}"
            )

        review_data = review_response.json()

        # PRをマージ
        merge_url = f"{GITHUB_API_BASE}/repos/{owner}/{request.repository}/pulls/{target_pr_number}/merge"
        merge_payload = {"merge_method": request.merge_method}

        if request.commit_title:
            merge_payload["commit_title"] = request.commit_title

        if request.commit_message:
            merge_payload["commit_message"] = request.commit_message

        merge_response = await client.put(merge_url, headers=get_headers(), json=merge_payload)

        if merge_response.status_code != 200:
            raise HTTPException(
                status_code=merge_response.status_code,
                detail=f"Pull Requestのマージに失敗しました: {merge_response.text}"
            )

        merge_data = merge_response.json()

        return {
            "success": True,
            "message": "Pull Requestを承認してマージしました",
            "data": {
                "pr_number": target_pr_number,
                "approval": {
                    "review_id": review_data["id"],
                    "state": review_data["state"],
                    "submitted_at": review_data["submitted_at"]
                },
                "merge": {
                    "sha": merge_data["sha"],
                    "merged": merge_data["merged"],
                    "message": merge_data["message"]
                }
            }
        }


# ヘルスチェックエンドポイント
@app.get("/")
async def root():
    """ヘルスチェックとAPI情報"""
    return {
        "message": "GitHub APIサービスが稼働中です",
        "version": "1.0.0",
        "endpoints": {
            "POST /create-issue": "GitHubのIssueを作成し、自動的にコメントを追加",
            "POST /create-pr": "Pull Requestを作成",
            "POST /approve-merge-pr": "Pull Requestを承認してマージ"
        },
        "environment": {
            "github_token_set": bool(GITHUB_TOKEN),
            "github_owner_set": bool(GITHUB_OWNER),
            "github_owner": GITHUB_OWNER if GITHUB_OWNER else None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
