#!/usr/bin/env python3
"""
Repository Service
Handles repository operations with task tracking
"""

import asyncio
from typing import Dict, Any, Callable, Optional
from api.services.github_service import github_service
import logging

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for repository operations"""

    async def scan_repository(
        self,
        token: str,
        owner: str,
        repo: str,
        update_progress: Callable,
    ) -> Dict[str, Any]:
        """
        Scan a repository and collect metadata

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            update_progress: Callback to update progress

        Returns:
            Repository scan result
        """
        try:
            # Get repository details (25%)
            await update_progress(25, "Fetching repository details...")
            repo_data = await github_service.get_repository(token, owner, repo)

            # Get branches (50%)
            await update_progress(50, "Fetching branches...")
            branches = await github_service.list_branches(token, owner, repo)

            # Get root files (75%)
            await update_progress(75, "Fetching file structure...")
            files = await github_service.list_repository_files(
                token, owner, repo, "", repo_data.get("default_branch", "main")
            )

            # Compile results
            await update_progress(90, "Processing results...")

            result = {
                "repository": repo_data,
                "branches": branches,
                "root_files": files,
                "file_count": len(files),
                "branch_count": len(branches),
                "scan_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }

            await update_progress(100, "Scan complete")

            return result

        except Exception as e:
            logger.error(f"Repository scan failed: {e}")
            raise

    async def analyze_repository_structure(
        self,
        token: str,
        owner: str,
        repo: str,
        max_depth: int = 3,
        update_progress: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Analyze repository structure recursively

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            max_depth: Maximum directory depth to scan
            update_progress: Callback to update progress

        Returns:
            Repository structure analysis
        """
        try:
            repo_data = await github_service.get_repository(token, owner, repo)
            default_branch = repo_data.get("default_branch", "main")

            # Build file tree
            file_tree = await self._build_file_tree(
                token,
                owner,
                repo,
                "",
                default_branch,
                max_depth,
                update_progress,
            )

            return {
                "repository": repo_data,
                "file_tree": file_tree,
                "analysis_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Repository structure analysis failed: {e}")
            raise

    async def _build_file_tree(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str,
        branch: str,
        max_depth: int,
        update_progress: Optional[Callable],
        current_depth: int = 0,
    ) -> Dict[str, Any]:
        """
        Build file tree recursively

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name
            path: Current path
            branch: Branch name
            max_depth: Maximum depth
            update_progress: Progress callback
            current_depth: Current depth

        Returns:
            File tree structure
        """
        try:
            files = await github_service.list_repository_files(
                token, owner, repo, path, branch
            )

            result = {
                "name": path.split("/")[-1] if path else repo,
                "path": path,
                "type": "dir",
                "children": [],
            }

            for file in files:
                if file["type"] == "dir" and current_depth < max_depth:
                    # Recursively process directories
                    sub_tree = await self._build_file_tree(
                        token,
                        owner,
                        repo,
                        file["path"],
                        branch,
                        max_depth,
                        update_progress,
                        current_depth + 1,
                    )
                    result["children"].append(sub_tree)
                else:
                    # Add file
                    result["children"].append(
                        {
                            "name": file["name"],
                            "path": file["path"],
                            "type": file["type"],
                            "size": file["size"],
                        }
                    )

            return result

        except Exception as e:
            logger.error(f"Failed to build file tree for {path}: {e}")
            raise

    async def get_repository_stats(
        self,
        token: str,
        owner: str,
        repo: str,
    ) -> Dict[str, Any]:
        """
        Get repository statistics

        Args:
            token: GitHub API token
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository statistics
        """
        try:
            repo_data = await github_service.get_repository(token, owner, repo)

            return {
                "name": repo_data.get("name", ""),
                "description": repo_data.get("description", ""),
                "url": repo_data.get("url", ""),
                "language": repo_data.get("language", ""),
                "stars": repo_data.get("stars", 0),
                "forks": repo_data.get("forks", 0),
                "watchers": repo_data.get("watchers", 0),
                "created_at": repo_data.get("created_at", ""),
                "updated_at": repo_data.get("updated_at", ""),
            }

        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            raise


# Global repository service instance
repository_service = RepositoryService()
