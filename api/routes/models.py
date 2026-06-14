#!/usr/bin/env python3
"""
Model Discovery Routes
Handles model discovery and metadata retrieval from Hugging Face Hub
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from api.services.model_discovery import model_discovery_service, CodeModel

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelMetadata(BaseModel):
    """Model metadata response"""
    model_id: str
    name: str
    description: Optional[str]
    downloads: int
    likes: int
    tags: List[str]
    url: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    architecture: Optional[str] = None


class ModelsListResponse(BaseModel):
    """Response containing list of models"""
    models: List[ModelMetadata]
    total: int
    search_query: Optional[str] = None


@router.get("/discover", response_model=ModelsListResponse)
async def discover_models(
    search: Optional[str] = Query(None, description="Search query for models"),
    limit: int = Query(20, description="Maximum number of models to return", ge=1, le=100),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> ModelsListResponse:
    """
    Discover code generation models from Hugging Face Hub

    Args:
        search: Optional search query (e.g., "code", "llama", "python")
        limit: Number of models to return (1-100)
        refresh: Force refresh cache

    Returns:
        List of available code models with metadata
    """
    try:
        models = await model_discovery_service.discover_code_models(
            limit=limit,
            search_query=search,
            force_refresh=refresh
        )

        return ModelsListResponse(
            models=[ModelMetadata(**model.to_dict()) for model in models],
            total=len(models),
            search_query=search,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model discovery failed: {str(e)}"
        )


@router.get("/popular", response_model=ModelsListResponse)
async def get_popular_models() -> ModelsListResponse:
    """
    Get popular code generation models

    Returns:
        Curated list of popular models
    """
    try:
        models = await model_discovery_service.get_popular_code_models()

        return ModelsListResponse(
            models=[ModelMetadata(**model.to_dict()) for model in models],
            total=len(models),
            search_query="popular",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch popular models: {str(e)}"
        )


@router.get("/info/{model_id:path}", response_model=ModelMetadata)
async def get_model_info(model_id: str) -> ModelMetadata:
    """
    Get detailed information about a specific model

    Args:
        model_id: Model ID (e.g., 'deepseek-coder/deepseek-coder-1b-base')

    Returns:
        Detailed model metadata
    """
    try:
        model = await model_discovery_service.get_model_details(model_id)

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found"
            )

        return ModelMetadata(**model.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch model info: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_model_cache() -> dict:
    """
    Clear the model discovery cache

    Returns:
        Success message
    """
    try:
        model_discovery_service.clear_cache()
        return {"message": "Model cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
