#!/usr/bin/env python3
"""
Repository Routes
Handles repository listing, browsing, and file operations
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from api.services.github_service import github_service
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


class ListRepositoriesRequest(BaseModel):
    """Repository list request"""
    token: str = Field(..., min_length=1, max_length=500)
    per_page: int = Field(default=50, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    sort: str = Field(default="updated")


class RepositoryDetailsRequest(BaseModel):
    """Repository details request"""
    token: str = Field(..., min_length=1, max_length=500)
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)


class RepositoryFilesRequest(BaseModel):
    """Repository files request"""
    token: str = Field(..., min_length=1, max_length=500)
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)
    path: str = Field(default="", max_length=1000)
    branch: str = Field(default="main", max_length=255)


class FileContentRequest(BaseModel):
    """File content request"""
    token: str = Field(..., min_length=1, max_length=500)
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1, max_length=1000)
    branch: str = Field(default="main", max_length=255)


class BranchesRequest(BaseModel):
    """Branches list request"""
    token: str = Field(..., min_length=1, max_length=500)
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)


async def get_current_user(session_token: str = Cookie(None)):
    """Dependency to get current user from session"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


@router.post("/list")
async def list_repositories(
    request: ListRepositoriesRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List user repositories

    Args:
        request: Repository list request with token

    Returns:
        List of repositories
    """
    try:
        repos = await github_service.list_repositories(
            token=request.token,
            per_page=request.per_page,
            page=request.page,
            sort=request.sort
        )
        return {"repositories": repos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/get")
async def get_repository(
    request: RepositoryDetailsRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get repository details

    Args:
        request: Repository details request

    Returns:
        Repository information
    """
    try:
        repo = await github_service.get_repository(
            token=request.token,
            owner=request.owner,
            repo=request.repo
        )
        return repo
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/files")
async def list_repository_files(
    request: RepositoryFilesRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List files in repository directory

    Args:
        request: File list request

    Returns:
        List of files
    """
    try:
        files = await github_service.list_repository_files(
            token=request.token,
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            branch=request.branch
        )
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/file")
async def get_file_content(
    request: FileContentRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get file content

    Args:
        request: File content request

    Returns:
        File information with content
    """
    try:
        file_info = await github_service.get_file_content(
            token=request.token,
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            branch=request.branch
        )
        return file_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/branches")
async def list_branches(
    request: BranchesRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List repository branches

    Args:
        request: Branches list request

    Returns:
        List of branches
    """
    try:
        branches = await github_service.list_branches(
            token=request.token,
            owner=request.owner,
            repo=request.repo
        )
        return {"branches": branches}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-token")
async def validate_token(
    request: RepositoryDetailsRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Validate GitHub API token

    Args:
        request: Request with token

    Returns:
        Validation result
    """
    is_valid = await github_service.validate_token(request.token)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid GitHub token")
    return {"valid": True}
