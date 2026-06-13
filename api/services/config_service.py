#!/usr/bin/env python3
"""
Configuration Service
Manages user preferences and API key storage
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class ConfigurationService:
    """Manages user configurations and settings"""

    def __init__(self):
        """Initialize configuration service"""
        # In-memory store (would use database in production)
        self.user_configs: Dict[str, Dict[str, Any]] = {}
        self.user_secrets: Dict[str, Dict[str, str]] = {}

    def get_config(self, user_id: int) -> Dict[str, Any]:
        """
        Get user configuration

        Args:
            user_id: User ID

        Returns:
            User configuration dict
        """
        return self.user_configs.get(
            str(user_id),
            {
                "preferred_model": "claude-3-5-sonnet-20241022",
                "preferred_provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 4096,
                "theme": "auto",
                "notifications_enabled": True,
                "auto_save": True,
            },
        )

    def update_config(self, user_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user configuration

        Args:
            user_id: User ID
            config: Configuration updates

        Returns:
            Updated configuration
        """
        user_id_str = str(user_id)
        current = self.get_config(user_id)

        # Validate temperature
        if "temperature" in config:
            config["temperature"] = max(0.0, min(2.0, config["temperature"]))

        # Validate max_tokens
        if "max_tokens" in config:
            config["max_tokens"] = max(1, min(128000, config["max_tokens"]))

        current.update(config)
        self.user_configs[user_id_str] = current

        return current

    def store_api_key(self, user_id: int, provider: str, api_key: str) -> bool:
        """
        Store encrypted API key (in production, use cryptography library)

        Args:
            user_id: User ID
            provider: Provider name (anthropic, groq, huggingface, etc)
            api_key: API key

        Returns:
            True if stored successfully
        """
        user_id_str = str(user_id)

        if user_id_str not in self.user_secrets:
            self.user_secrets[user_id_str] = {}

        # In production, encrypt the API key
        self.user_secrets[user_id_str][provider] = api_key

        return True

    def get_api_key(self, user_id: int, provider: str) -> Optional[str]:
        """
        Get stored API key (in production, decrypt it)

        Args:
            user_id: User ID
            provider: Provider name

        Returns:
            API key or None if not stored
        """
        user_id_str = str(user_id)

        if user_id_str not in self.user_secrets:
            return None

        return self.user_secrets[user_id_str].get(provider)

    def list_api_keys(self, user_id: int) -> Dict[str, str]:
        """
        List all stored API keys (without showing actual keys)

        Args:
            user_id: User ID

        Returns:
            Dict with provider as key and masked key info as value
        """
        user_id_str = str(user_id)

        if user_id_str not in self.user_secrets:
            return {}

        return {
            provider: f"{provider}_key_stored"
            for provider in self.user_secrets[user_id_str].keys()
        }

    def delete_api_key(self, user_id: int, provider: str) -> bool:
        """
        Delete stored API key

        Args:
            user_id: User ID
            provider: Provider name

        Returns:
            True if deleted successfully
        """
        user_id_str = str(user_id)

        if user_id_str in self.user_secrets and provider in self.user_secrets[user_id_str]:
            del self.user_secrets[user_id_str][provider]
            return True

        return False

    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """
        Validate API key format (basic check)

        Args:
            provider: Provider name
            api_key: API key to validate

        Returns:
            True if format is valid
        """
        if not api_key or len(api_key) < 10:
            return False

        # Provider-specific validation
        if provider == "anthropic":
            return api_key.startswith("sk-")
        elif provider == "groq":
            return len(api_key) > 20
        elif provider == "huggingface":
            return api_key.startswith("hf_") and len(api_key) > 10
        elif provider == "openai":
            return api_key.startswith("sk-") and len(api_key) > 20

        return True  # Unknown provider, basic check passed


# Global configuration service instance
config_service = ConfigurationService()
