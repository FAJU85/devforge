#!/usr/bin/env python3
"""
Base Provider Class
Defines interface for all LLM providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncIterator, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Provider configuration"""

    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    timeout: int = 30


@dataclass
class MessageUsage:
    """Token usage information"""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ProviderResponse:
    """Standard response from provider"""

    content: str
    usage: MessageUsage
    model: str
    provider: str
    stop_reason: Optional[str] = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str):
        """
        Initialize provider

        Args:
            api_key: API key for authentication
        """
        self.api_key = api_key
        self.config = ProviderConfig()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Get list of supported models"""
        pass

    def set_config(self, **kwargs) -> None:
        """
        Update provider configuration

        Args:
            **kwargs: Configuration parameters
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> ProviderResponse:
        """
        Generate a response from messages

        Args:
            messages: List of messages with 'role' and 'content'
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            ProviderResponse with content and usage info
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a response from messages

        Args:
            messages: List of messages with 'role' and 'content'
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens for text

        Args:
            text: Text to count tokens for
            model: Optional model to use for counting

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> int:
        """
        Count tokens for a list of messages

        Args:
            messages: List of messages
            model: Optional model to use for counting

        Returns:
            Number of tokens
        """
        pass

    async def validate_connection(self) -> bool:
        """
        Validate API connection

        Returns:
            True if connection is valid
        """
        try:
            # Try to count tokens as a simple validation
            self.count_tokens("test")
            return True
        except Exception:
            return False

    def handle_error(self, error: Exception) -> str:
        """
        Handle and format provider errors

        Args:
            error: The error that occurred

        Returns:
            Formatted error message
        """
        error_msg = str(error)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return "Authentication failed. Please check your API key."
        elif "rate" in error_msg.lower():
            return "Rate limit exceeded. Please try again later."
        elif "timeout" in error_msg.lower():
            return "Request timeout. Please try again."
        else:
            return f"Provider error: {error_msg}"
