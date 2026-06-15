#!/usr/bin/env python3
"""
Code Generation Routes
Handles AI-powered code generation and modification
"""

from fastapi import APIRouter, HTTPException, Cookie
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import difflib
import asyncio
import os
import logging
from api.services.github_service import github_service
from api.services.providers import ProviderFactory
from api.services.auth_service import auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generate", tags=["generate"])

# Get HF token from environment
HF_TOKEN = os.environ.get("HF_TOKEN", "")


def get_api_key_for_provider(provider: str, session_token: Optional[str] = None) -> str:
    """Return the API key for the given provider.

    For huggingface: prefers the user's own token from their HF OAuth session,
    then falls back to the Space-level HF_TOKEN env var.
    For other providers: reads from env vars.
    """
    if provider.lower() == "huggingface":
        # 1. User's own token from HF OAuth session
        if session_token:
            user_token = auth_service.get_hf_token_from_session(session_token)
            if user_token:
                return user_token
        # 2. Fall back to Space-level token
        key = os.environ.get("HF_TOKEN", "")
        if key:
            return key
        raise ValueError(
            "No HF token available. Sign in with Hugging Face or set HF_TOKEN."
        )

    env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    env_var = env_map.get(provider.lower())
    if not env_var:
        raise ValueError(f"Unsupported provider: {provider}")
    key = os.environ.get(env_var, "")
    if not key:
        raise ValueError(f"{env_var} environment variable is required for provider '{provider}'")
    return key


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
    session_token: Optional[str] = None,
) -> tuple[str, Optional[int]]:
    """Generate code using a specific model, return code and token count"""
    try:
        api_key = get_api_key_for_provider(provider, session_token)

        provider_instance = provider_factory.create_provider(provider, api_key)

        # Format prompt as messages for the provider
        messages = [{"role": "user", "content": prompt}]

        # Generate response using the provider
        response = await provider_instance.generate(
            messages=messages,
            model=model,
            max_tokens=4000,
            temperature=0.3,
        )

        # Extract token count from usage
        tokens_used = response.usage.total_tokens if response.usage else None

        return response.content.strip(), tokens_used
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating with model {model}: {error_msg}")
        raise Exception(f"Model {model} failed: {error_msg}")


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

        # Generate modified code using the provider with provider-specific API key
        try:
            api_key = get_api_key_for_provider(request.provider)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))

        provider_factory = ProviderFactory()
        provider = provider_factory.create_provider(request.provider, api_key)

        # Format prompt as messages
        messages = [{"role": "user", "content": prompt}]

        response = await provider.generate(
            messages=messages,
            model=request.model,
            max_tokens=4000,
            temperature=0.3,  # Lower temperature for more deterministic code
        )

        modified_code = response.content.strip()

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
async def generate_code_parallel(
    request: MultiModelCodeGenerationRequest,
    session_token: Optional[str] = Cookie(None),
) -> MultiModelCodeGenerationResponse:
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

        # Validate provider API key is configured before launching tasks
        try:
            get_api_key_for_provider(request.provider, session_token)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Build ordered list of (model, task) tuples so duplicate model names
        # in request.models still produce one task each.
        provider_factory = ProviderFactory()
        model_tasks: List[tuple] = []
        for model in request.models:
            task = generate_code_with_model(
                provider_factory,
                request.provider,
                model,
                prompt,
                session_token,
            )
            model_tasks.append((model, task))

        # Execute all tasks concurrently
        results = []
        task_coroutines = [task for _, task in model_tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Process results
        for (model, _), task_result in zip(model_tasks, task_results):
            try:
                if isinstance(task_result, Exception):
                    raise task_result

                modified_code, tokens_used = task_result
                diff = generate_diff(file_content, modified_code, request.file_path)
                results.append(MultiModelResult(
                    model=model,
                    original_code=file_content,
                    modified_code=modified_code,
                    diff=diff,
                    tokens_used=tokens_used,
                ))
            except Exception as e:
                logger.error(f"Error with model {model}: {str(e)}")
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
