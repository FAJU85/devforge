#!/usr/bin/env python3
"""
LLM Provider implementations
Handles Claude, Groq, and Hugging Face integrations
"""

from api.services.providers.base import BaseProvider
from api.services.providers.anthropic_provider import AnthropicProvider
from api.services.providers.groq_provider import GroqProvider
from api.services.providers.huggingface_provider import HuggingFaceProvider


class ProviderFactory:
    """Factory for creating LLM provider instances"""

    _providers = {
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,  # Alias
        "groq": GroqProvider,
        "huggingface": HuggingFaceProvider,
        "hf": HuggingFaceProvider,  # Alias
    }

    @classmethod
    def create_provider(cls, provider_name: str, api_key: str) -> BaseProvider:
        """
        Create a provider instance

        Args:
            provider_name: Name of the provider
            api_key: API key for the provider

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )

        return provider_class(api_key)

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported providers"""
        return list(cls._providers.keys())


__all__ = [
    "BaseProvider",
    "AnthropicProvider",
    "GroqProvider",
    "HuggingFaceProvider",
    "ProviderFactory",
]
