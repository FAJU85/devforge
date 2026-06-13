#!/usr/bin/env python3
"""
Groq Provider Implementation
Handles Groq API integration with Mixtral models
"""

from typing import Dict, List, AsyncIterator, Optional
from api.services.providers.base import BaseProvider, ProviderResponse, MessageUsage

# Try to import groq, but don't fail if not available
try:
    from groq import Groq as GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    GroqClient = None


class GroqProvider(BaseProvider):
    """Groq API provider implementation"""

    # Model information
    SUPPORTED_MODELS = [
        "mixtral-8x7b-32768",
        "mixtral-8x7b",
        "llama-2-70b-chat",
        "llama-2-13b-chat",
    ]

    def __init__(self, api_key: str):
        """Initialize Groq provider"""
        super().__init__(api_key)

        if not GROQ_AVAILABLE:
            raise RuntimeError(
                "Groq library not installed. Install it with: pip install groq"
            )

        self.client = GroqClient(api_key=api_key)

    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return "groq"

    @property
    def supported_models(self) -> List[str]:
        """Get supported models"""
        return self.SUPPORTED_MODELS

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> ProviderResponse:
        """
        Generate a response using Groq

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            ProviderResponse with content and usage
        """
        try:
            # Extract parameters from kwargs or config
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            top_p = kwargs.get("top_p", self.config.top_p)

            # Call Groq API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            # Extract usage information
            usage = MessageUsage(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            # Extract content
            content = response.choices[0].message.content if response.choices else ""

            # Get finish reason
            stop_reason = response.choices[0].finish_reason if response.choices else None

            return ProviderResponse(
                content=content,
                usage=usage,
                model=model,
                provider=self.provider_name,
                stop_reason=stop_reason,
            )

        except Exception as error:
            raise RuntimeError(f"Groq API error: {self.handle_error(error)}")

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a response from Groq

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        try:
            # Extract parameters from kwargs or config
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            top_p = kwargs.get("top_p", self.config.top_p)

            # Stream response from Groq
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as error:
            error_msg = self.handle_error(error)
            yield f"[ERROR] {error_msg}"

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens for Groq models

        Args:
            text: Text to count
            model: Model to use for counting

        Returns:
            Number of tokens (estimate)
        """
        try:
            # Groq models use similar tokenization to Llama
            # Rough estimate: ~1 token per 4 characters for English
            token_count = len(text) // 4

            # Ensure minimum of 1 token
            return max(1, token_count)

        except Exception:
            return max(1, len(text) // 4)

    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> int:
        """
        Count tokens for messages

        Args:
            messages: List of messages
            model: Model to use for counting

        Returns:
            Total tokens
        """
        try:
            # Convert messages to text and count
            text = ""
            for msg in messages:
                # Add role and separator tokens
                text += msg.get("role", "") + ": " + msg.get("content", "") + "\n"

            # Add overhead for message formatting (roughly 4-5 tokens per message)
            overhead = len(messages) * 5
            return self.count_tokens(text, model) + overhead

        except Exception:
            # Fallback
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return max(1, total_chars // 4)
