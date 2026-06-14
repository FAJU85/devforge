#!/usr/bin/env python3
"""
Model Discovery Service
Discovers and manages code generation models from Hugging Face Hub
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
from huggingface_hub import list_models, model_info, ModelInfo
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeModel:
    """Represents a code generation model from Hugging Face Hub"""
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "description": self.description,
            "downloads": self.downloads,
            "likes": self.likes,
            "tags": self.tags,
            "url": self.url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "architecture": self.architecture,
        }


class ModelDiscoveryService:
    """Service for discovering code generation models"""

    def __init__(self, cache_ttl_seconds: int = 3600):
        """
        Initialize the model discovery service

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, tuple[List[CodeModel], float]] = {}
        self._popular_models = [
            "bigcode/starcoder",
            "bigcode/starcoder2-15b",
            "mistralai/Mistral-7B-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "WizardLM/WizardCoder-15B-V1.0",
        ]

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False

        cached_data, timestamp = self._cache[key]
        age = datetime.now().timestamp() - timestamp
        return age < self.cache_ttl_seconds

    async def discover_code_models(
        self,
        limit: int = 20,
        search_query: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[CodeModel]:
        """
        Discover code generation models from Hugging Face Hub

        Args:
            limit: Maximum number of models to return
            search_query: Optional search query to filter models
            force_refresh: Force refresh cache

        Returns:
            List of discovered CodeModel objects
        """
        cache_key = f"models_{search_query}_{limit}"

        # Return cached results if valid
        if not force_refresh and self._is_cache_valid(cache_key):
            cached_data, _ = self._cache[cache_key]
            return cached_data

        try:
            # Search for code-related models on HF Hub
            query = search_query or "code"

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            models_generator = await loop.run_in_executor(
                None,
                lambda: list_models(
                    search=query,
                    sort="likes",
                    limit=limit,
                )
            )

            models_list = []
            for model_info_obj in models_generator:
                try:
                    code_model = self._convert_model_info(model_info_obj)
                    models_list.append(code_model)
                    if len(models_list) >= limit:
                        break
                except Exception as e:
                    logger.warning(f"Failed to process model {model_info_obj.id}: {e}")
                    continue

            # Cache the results
            self._cache[cache_key] = (models_list, datetime.now().timestamp())

            return models_list

        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return []

    async def get_popular_code_models(self) -> List[CodeModel]:
        """Get a curated list of popular code models"""
        models = []

        for model_id in self._popular_models:
            try:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda mid=model_id: model_info(mid)
                )
                code_model = self._convert_model_info(info)
                models.append(code_model)
            except Exception as e:
                logger.warning(f"Failed to fetch {model_id}: {e}")
                continue

        return models

    async def get_model_details(self, model_id: str) -> Optional[CodeModel]:
        """
        Get detailed information about a specific model

        Args:
            model_id: Model ID on Hugging Face Hub

        Returns:
            CodeModel object or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: model_info(model_id)
            )
            return self._convert_model_info(info)
        except Exception as e:
            logger.error(f"Error fetching model {model_id}: {e}")
            return None

    @staticmethod
    def _convert_model_info(info: ModelInfo) -> CodeModel:
        """Convert ModelInfo object to CodeModel"""
        return CodeModel(
            model_id=info.id,
            name=info.id.split("/")[-1],  # Use repo name as display name
            description=getattr(info, 'description', None) or "",
            downloads=getattr(info, 'downloads', 0) or 0,
            likes=getattr(info, 'likes', 0) or 0,
            tags=getattr(info, 'tags', None) or [],
            url=f"https://huggingface.co/{info.id}",
            created_at=str(getattr(info, 'created_at', None)) if getattr(info, 'created_at', None) else None,
            updated_at=str(getattr(info, 'last_modified', None)) if getattr(info, 'last_modified', None) else None,
            architecture=getattr(info, 'library_name', None) or None,
        )

    def clear_cache(self) -> None:
        """Clear all cached model data"""
        self._cache.clear()


# Global instance
model_discovery_service = ModelDiscoveryService()
