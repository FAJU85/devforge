#!/usr/bin/env python3
"""
Code Generation Routes
Handles AI-powered code generation and modification
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import difflib
import asyncio
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


class MultiModelCodeGenerationRequest(BaseModel):
    """Request to generate/modify code with multiple models"""
    repo_url: str
    file_path: str
    instruction: str
    github_token: str
    models: List[str] = ["deepseek-coder"]
    provider: str = "huggingface"


class MultiModelResult(BaseModel):
    """Single result from multi-model generation"""
    model: str
    original_code: str
    modified_code: str
    diff: str
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class MultiModelCodeGenerationResponse(BaseModel):
    """Response with results from multiple models"""
    original_code: str
    instruction: str
    results: List[MultiModelResult]
    models: List[str]
    provider: str


def generate_diff(original: str, modified: str, file_path: str) -> str:
    """Generate unified diff between original and modified code"""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = ''.join(difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=''
    ))
    return diff


async def generate_code_with_model(
    provider_factory: ProviderFactory,
    provider: str,
    model: str,
    prompt: str,
) -> tuple[str, Optional[int]]:
    """Generate code using a specific model, return code and token count"""
    try:
        provider_instance = provider_factory.create_provider(provider, model)
        response = await provider_instance.complete(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.3,
        )
        return response.text.strip(), getattr(response, 'tokens_used', None)
    except Exception as e:
        raise Exception(f"Model {model} failed: {str(e)}")


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


@router.post("/code-parallel", response_model=MultiModelCodeGenerationResponse)
async def generate_code_parallel(request: MultiModelCodeGenerationRequest) -> MultiModelCodeGenerationResponse:
    """
    Generate/modify code using multiple models in parallel

    Args:
        request: Request with repo URL, file path, instruction, and list of models

    Returns:
        Results from all models with original code and diffs
    """
    try:
        # Extract repo owner/name from URL
        if "github.com" not in request.repo_url:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")

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

        # Create prompt for the models
        prompt = f"""You are a code modification assistant. You will receive code and an instruction,
and you should return ONLY the modified code without any explanation or markdown formatting.

File: {request.file_path}
Instruction: {request.instruction}

Original code:
```
{file_content}
```

Modified code:"""

        # Create tasks for parallel execution
        provider_factory = ProviderFactory()
        tasks = []
        for model in request.models:
            task = generate_code_with_model(
                provider_factory,
                request.provider,
                model,
                prompt
            )
            tasks.append((model, task))

        # Run all models in parallel
        results = []
        for model, task in tasks:
            try:
                modified_code, tokens_used = await task
                diff = generate_diff(file_content, modified_code, request.file_path)
                results.append(MultiModelResult(
                    model=model,
                    original_code=file_content,
                    modified_code=modified_code,
                    diff=diff,
                    tokens_used=tokens_used,
                ))
            except Exception as e:
                results.append(MultiModelResult(
                    model=model,
                    original_code=file_content,
                    modified_code="",
                    diff="",
                    error=str(e),
                ))

        return MultiModelCodeGenerationResponse(
            original_code=file_content,
            instruction=request.instruction,
            results=results,
            models=request.models,
            provider=request.provider,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-model generation failed: {str(e)}"
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
