#!/usr/bin/env python3
"""
Anthropic Provider Implementation
Handles Claude API integration
"""

import anthropic
from typing import Dict, List, AsyncIterator, Optional
from api.services.providers.base import BaseProvider, ProviderResponse, MessageUsage


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation"""

    # Model information
    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20250219",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    # Approximate token counts per model (for offline counting)
    # These are estimates - use API for exact counts when available
    TOKEN_ESTIMATES = {
        "claude-3-5-sonnet": 150000,  # Input tokens limit
        "claude-3-5-haiku": 200000,   # Input tokens limit
        "claude-3-opus": 200000,      # Input tokens limit
        "claude-3-sonnet": 200000,    # Input tokens limit
        "claude-3-haiku": 200000,     # Input tokens limit
    }

    def __init__(self, api_key: str):
        """Initialize Anthropic provider"""
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return "anthropic"

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
        Generate a response using Claude

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

            # Call Claude API
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                messages=messages,
            )

            # Extract usage information
            usage = MessageUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            # Extract content
            content = response.content[0].text if response.content else ""

            # Determine stop reason
            stop_reason = response.stop_reason if hasattr(response, "stop_reason") else None

            return ProviderResponse(
                content=content,
                usage=usage,
                model=model,
                provider=self.provider_name,
                stop_reason=stop_reason,
            )

        except Exception as error:
            raise RuntimeError(f"Claude API error: {self.handle_error(error)}")

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a response from Claude

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

            # Stream response from Claude
            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as error:
            error_msg = self.handle_error(error)
            yield f"[ERROR] {error_msg}"

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens using Claude's token counter

        Args:
            text: Text to count
            model: Model to use for counting

        Returns:
            Number of tokens
        """
        try:
            if not model:
                model = self.SUPPORTED_MODELS[0]

            # Use Anthropic's token counter from the SDK
            # The count_tokens method from the Anthropic SDK provides accurate counting
            if hasattr(self.client, 'count_tokens'):
                return self.client.count_tokens(text)
            else:
                # Fallback for older SDK versions - use client's built-in method
                # Claude uses approximately 3-4 characters per token on average
                token_count = len(text) // 4
                return max(1, token_count)

        except Exception:
            # Fallback to character-based estimation
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
            if not model:
                model = self.SUPPORTED_MODELS[0]

            # Try using Anthropic's message token counting if available
            if hasattr(self.client, 'count_tokens'):
                # Convert messages to the format Anthropic expects
                text = ""
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    text += f"{role}: {content}\n"
                return self.client.count_tokens(text)
            else:
                # Fallback: convert messages to text and count
                text = ""
                for msg in messages:
                    text += msg.get("role", "") + ": " + msg.get("content", "") + "\n"

                # Add overhead for message formatting (roughly 4 tokens per message)
                overhead = len(messages) * 4
                return self.count_tokens(text, model) + overhead

        except Exception:
            # Fallback to simple character counting
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return max(1, total_chars // 4)
