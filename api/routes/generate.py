#!/usr/bin/env python3
"""
Code Generation Routes
Handles AI-powered code generation and modification
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import difflib
from api.services.github_service import github_service
from api.services.providers import ProviderFactory

router = APIRouter(prefix="/api/generate", tags=["generate"])


class CodeGenerationRequest(BaseModel):
    """Request to generate/modify code"""
    repo_url: str
    file_path: str
    instruction: str
    github_token: str
    model: str = "deepseek-coder"
    provider: str = "huggingface"


class CodeGenerationResponse(BaseModel):
    """Response with original and modified code"""
    original_code: str
    modified_code: str
    diff: str
    instruction: str
    model: str
    provider: str


class CreatePRRequest(BaseModel):
    """Request to create a GitHub PR"""
    repo_url: str
    file_path: str
    modified_code: str
    title: str
    description: str
    github_token: str
    branch_name: Optional[str] = None


class CreatePRResponse(BaseModel):
    """Response with PR details"""
    pr_url: str
    pr_number: int
    branch_name: str


@router.post("/code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest) -> CodeGenerationResponse:
    """
    Generate or modify code using a Hugging Face model

    Args:
        request: Code generation request with repo URL, file path, instruction, and model

    Returns:
        Original code, modified code, and diff
    """
    try:
        # Extract repo owner/name from URL
        # Handle both https://github.com/owner/repo and git@github.com:owner/repo formats
        if "github.com" not in request.repo_url:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")

        # Parse owner/repo from URL
        parts = request.repo_url.replace(".git", "").split("/")
        owner = parts[-2]
        repo = parts[-1]

        # Get file content from GitHub
        file_response = await github_service.get_file_content(
            token=request.github_token,
            owner=owner,
            repo=repo,
            path=request.file_path
        )
        file_content = file_response.get("content", "")

        if not file_content:
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        # Create prompt for the model
        prompt = f"""You are a code modification assistant. You will receive code and an instruction,
and you should return ONLY the modified code without any explanation or markdown formatting.

File: {request.file_path}
Instruction: {request.instruction}

Original code:
```
{file_content}
```

Modified code:"""

        # Generate modified code using the provider
        provider_factory = ProviderFactory()
        provider = provider_factory.create_provider(request.provider, request.model)

        response = await provider.complete(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.3,  # Lower temperature for more deterministic code
        )

        modified_code = response.text.strip()

        # Generate diff
        original_lines = file_content.splitlines(keepends=True)
        modified_lines = modified_code.splitlines(keepends=True)
        diff = ''.join(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{request.file_path}",
            tofile=f"b/{request.file_path}",
            lineterm=''
        ))

        return CodeGenerationResponse(
            original_code=file_content,
            modified_code=modified_code,
            diff=diff,
            instruction=request.instruction,
            model=request.model,
            provider=request.provider,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code generation failed: {str(e)}"
        )


@router.post("/create-pr", response_model=CreatePRResponse)
async def create_pr(request: CreatePRRequest) -> CreatePRResponse:
    """
    Create a GitHub PR with the modified code

    Args:
        request: PR creation request with repo URL, file path, and modified code

    Returns:
        PR URL, number, and branch name
    """
    try:
        # Parse owner/repo from URL
        parts = request.repo_url.replace(".git", "").split("/")
        owner = parts[-2]
        repo = parts[-1]

        # Generate branch name if not provided
        branch_name = request.branch_name or f"devforge/modify-{request.file_path.replace('/', '-')}"

        # Create PR using GitHub service
        pr = await github_service.create_pull_request(
            token=request.github_token,
            owner=owner,
            repo=repo,
            title=request.title,
            description=request.description,
            file_path=request.file_path,
            file_content=request.modified_code,
            branch_name=branch_name,
        )

        return CreatePRResponse(
            pr_url=pr["html_url"],
            pr_number=pr["number"],
            branch_name=branch_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PR creation failed: {str(e)}"
        )
