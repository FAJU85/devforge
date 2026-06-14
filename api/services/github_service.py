#!/usr/bin/env python3
"""
GitHub Service
Integrates with GitHub API for repository operations
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor


class GitHubService:
    """GitHub API integration service"""

    BASE_URL = "https://api.github.com"
    TIMEOUT = 15

    def __init__(self):
        """Initialize GitHub service"""
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_headers(self, token: str) -> Dict[str, str]:
        """Build GitHub API request headers"""
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevForge/1.0"
        }

    async def get_user(self, token: str) -> Dict[str, Any]:
        """
        Get authenticated user info

        Args:
            token: GitHub API token

        Returns:
            User info dict
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers=self._get_headers(token),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch user: {str(e)}")

    async def list_repositories(
        self,
        token: str,
        per_page: int = 50,
        page: int = 1,
        sort: str = "updated"
    ) -> List[Dict[str, Any]]:
        """
        List user repositories

        Args:
            token: GitHub API token
            per_page: Items per page (1-100)
            page: Page number
            sort: Sort field (updated, stars, name)

        Returns:
            List of repository dicts
        """
        try:
            per_page = max(1, min(per_page, 100))
            response = requests.get(
                f"{self.BASE_URL}/user/repos",
                headers=self._get_headers(token),
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": sort,
                    "direction": "desc"
                },
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            repos = response.json()

            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name", ""),
                    "full_name": r.get("full_name", ""),
                    "description": r.get("description") or "",
                    "url": r.get("html_url", ""),
                    "private": r.get("private", False),
                    "language": r.get("language") or "",
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "updated_at": r.get("updated_at", ""),
                    "default_branch": r.get("default_branch", "main"),
                }
                for r in repos
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to list repositories: {str(e)}")

    async def get_repository(self, token: str, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository details

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository info dict
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self._get_headers(token),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            r = response.json()

            return {
                "id": r.get("id"),
                "name": r.get("name", ""),
                "full_name": r.get("full_name", ""),
                "description": r.get("description") or "",
                "url": r.get("html_url", ""),
                "private": r.get("private", False),
                "language": r.get("language") or "",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "watchers": r.get("watchers_count", 0),
                "updated_at": r.get("updated_at", ""),
                "created_at": r.get("created_at", ""),
                "default_branch": r.get("default_branch", "main"),
            }
        except requests.RequestException as e:
            raise Exception(f"Failed to get repository: {str(e)}")

    async def list_repository_files(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str = "",
        branch: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        List files in repository directory

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            path: Directory path (empty for root)
            branch: Branch name

        Returns:
            List of file dicts
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents"
            if path:
                url += f"/{path.lstrip('/')}"

            response = requests.get(
                url,
                headers=self._get_headers(token),
                params={"ref": branch},
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            items = response.json()

            # Handle single file response
            if isinstance(items, dict):
                items = [items]

            return [
                {
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "type": item.get("type", ""),  # file, dir, symlink
                    "size": item.get("size", 0),
                    "url": item.get("html_url", ""),
                    "download_url": item.get("download_url", "") if item.get("type") == "file" else None,
                }
                for item in items
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to list files: {str(e)}")

    async def get_file_content(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Get file content

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name

        Returns:
            File content dict
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path.lstrip('/')}",
                headers=self._get_headers(token),
                params={"ref": branch},
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            import base64
            content = ""
            if data.get("type") == "file":
                try:
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                except Exception:
                    content = "[Binary file - cannot display]"

            return {
                "name": data.get("name", ""),
                "path": data.get("path", ""),
                "size": data.get("size", 0),
                "type": data.get("type", ""),
                "content": content,
                "url": data.get("html_url", ""),
            }
        except requests.RequestException as e:
            raise Exception(f"Failed to get file: {str(e)}")

    async def list_branches(self, token: str, owner: str, repo: str) -> List[Dict[str, str]]:
        """
        List repository branches

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name

        Returns:
            List of branch dicts
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/branches",
                headers=self._get_headers(token),
                params={"per_page": 100},
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            branches = response.json()

            return [
                {
                    "name": b.get("name", ""),
                    "sha": (b.get("commit") or {}).get("sha", "")[:7],
                    "protected": b.get("protected", False),
                }
                for b in branches
            ]
        except requests.RequestException as e:
            raise Exception(f"Failed to list branches: {str(e)}")

    async def validate_token(self, token: str) -> bool:
        """
        Validate GitHub API token

        Args:
            token: GitHub API token

        Returns:
            True if valid
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers=self._get_headers(token),
                timeout=self.TIMEOUT
            )
            return response.status_code == 200
        except Exception:
            return False

    async def create_pull_request(
        self,
        token: str,
        owner: str,
        repo: str,
        title: str,
        description: str,
        file_path: str,
        file_content: str,
        branch_name: str = "devforge-changes"
    ) -> Dict[str, Any]:
        """
        Create a GitHub pull request with modified code

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            title: PR title
            description: PR description
            file_path: File to modify
            file_content: New file content
            branch_name: Branch name for the PR

        Returns:
            PR data dict with html_url and number
        """
        try:
            import base64

            # Step 1: Get current file content and SHA (needed for update)
            file_response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}",
                headers=self._get_headers(token),
                timeout=self.TIMEOUT
            )
            file_response.raise_for_status()
            file_data = file_response.json()
            file_sha = file_data.get("sha")

            # Step 2: Update file on a new branch
            update_response = requests.put(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}",
                headers=self._get_headers(token),
                json={
                    "message": f"DevForge: {title}",
                    "content": base64.b64encode(file_content.encode()).decode(),
                    "sha": file_sha,
                    "branch": branch_name,
                },
                timeout=self.TIMEOUT
            )
            update_response.raise_for_status()

            # Step 3: Create pull request
            pr_response = requests.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=self._get_headers(token),
                json={
                    "title": title,
                    "body": description,
                    "head": branch_name,
                    "base": "main",  # Default to main branch
                },
                timeout=self.TIMEOUT
            )
            pr_response.raise_for_status()
            pr_data = pr_response.json()

            return {
                "html_url": pr_data.get("html_url", ""),
                "number": pr_data.get("number", 0),
                "id": pr_data.get("id", 0),
                "head": pr_data.get("head", {}).get("ref", ""),
            }

        except requests.RequestException as e:
            raise Exception(f"Failed to create PR: {str(e)}")


# Global GitHub service instance
github_service = GitHubService()
