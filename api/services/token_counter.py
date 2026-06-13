#!/usr/bin/env python3
"""
Token Counter Service
Provides token counting for different providers and models
"""

from typing import Dict, List, Optional
from api.services.providers import ProviderFactory


class TokenCounter:
    """Handles token counting across providers"""

    def __init__(self):
        """Initialize token counter"""
        self._counters: Dict[str, object] = {}

    def count_text_tokens(
        self,
        text: str,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> int:
        """
        Count tokens for text

        Args:
            text: Text to count tokens for
            provider: Provider name
            model: Optional model name
            api_key: Optional API key for provider

        Returns:
            Number of tokens
        """
        try:
            if not api_key:
                # Return estimate without provider access
                return self._estimate_tokens(text, provider)

            # Create provider instance
            provider_instance = ProviderFactory.create_provider(provider, api_key)
            return provider_instance.count_tokens(text, model)

        except Exception:
            # Fall back to estimation
            return self._estimate_tokens(text, provider)

    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> int:
        """
        Count tokens for messages

        Args:
            messages: List of messages
            provider: Provider name
            model: Optional model name
            api_key: Optional API key for provider

        Returns:
            Number of tokens
        """
        try:
            if not api_key:
                # Return estimate without provider access
                return self._estimate_messages_tokens(messages, provider)

            # Create provider instance
            provider_instance = ProviderFactory.create_provider(provider, api_key)
            return provider_instance.count_messages_tokens(messages, model)

        except Exception:
            # Fall back to estimation
            return self._estimate_messages_tokens(messages, provider)

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: str,
        model: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Estimate cost for token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: Provider name
            model: Optional model name

        Returns:
            Dict with estimated costs
        """
        # Pricing as of 2024
        pricing_map = {
            "anthropic": {
                "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
                "claude-3-5-haiku": {"input": 0.00080, "output": 0.004},
                "claude-3-opus": {"input": 0.015, "output": 0.075},
                "default": {"input": 0.003, "output": 0.015},
            },
            "groq": {
                "mixtral-8x7b": {"input": 0.00024, "output": 0.00024},
                "llama-2-70b": {"input": 0.00075, "output": 0.00075},
                "default": {"input": 0.00024, "output": 0.00024},
            },
            "huggingface": {
                "default": {"input": 0, "output": 0},  # Free tier
            },
        }

        provider_pricing = pricing_map.get(provider.lower(), {"default": {"input": 0, "output": 0}})

        # Try to find model-specific pricing
        model_key = None
        if model:
            for key in provider_pricing:
                if key != "default" and key in model.lower():
                    model_key = key
                    break

        pricing = provider_pricing.get(model_key) if model_key else provider_pricing.get("default")

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "currency": "USD",
        }

    def _estimate_tokens(self, text: str, provider: str) -> int:
        """
        Estimate tokens using character-based heuristics

        Args:
            text: Text to estimate
            provider: Provider name

        Returns:
            Estimated token count
        """
        # Character-to-token ratios vary by provider/model
        ratio_map = {
            "anthropic": 3.5,  # Claude uses ~3.5 chars per token
            "groq": 4.0,       # Mixtral/Llama use ~4 chars per token
            "huggingface": 4.0,  # Generally ~4 chars per token
        }

        ratio = ratio_map.get(provider.lower(), 4.0)
        tokens = max(1, int(len(text.strip()) / ratio))
        return tokens

    def _estimate_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        provider: str
    ) -> int:
        """
        Estimate tokens for messages

        Args:
            messages: List of messages
            provider: Provider name

        Returns:
            Estimated token count
        """
        # Estimate content tokens
        content_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            content_tokens += self._estimate_tokens(content, provider)

        # Add overhead for message structure
        # Each message typically adds 4-5 tokens for role, separators, etc.
        overhead_per_message = 5
        structure_tokens = len(messages) * overhead_per_message

        return content_tokens + structure_tokens

    def get_token_limits(
        self,
        provider: str,
        model: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get token limits for provider/model

        Args:
            provider: Provider name
            model: Optional model name

        Returns:
            Dict with token limits
        """
        limits_map = {
            "anthropic": {
                "claude-3-5-sonnet": {"context": 200000, "max_output": 4096},
                "claude-3-5-haiku": {"context": 200000, "max_output": 4096},
                "claude-3-opus": {"context": 200000, "max_output": 4096},
                "default": {"context": 200000, "max_output": 4096},
            },
            "groq": {
                "mixtral-8x7b-32768": {"context": 32768, "max_output": 4096},
                "mixtral-8x7b": {"context": 8192, "max_output": 4096},
                "llama-2-70b": {"context": 4096, "max_output": 4096},
                "default": {"context": 8192, "max_output": 4096},
            },
            "huggingface": {
                "default": {"context": 8192, "max_output": 2048},
            },
        }

        provider_limits = limits_map.get(provider.lower(), {"default": {"context": 8192, "max_output": 4096}})

        # Try to find model-specific limits
        limits = {"context": 8192, "max_output": 4096}
        if model:
            for key in provider_limits:
                if key != "default" and key in model.lower():
                    limits = provider_limits[key]
                    break
            else:
                limits = provider_limits.get("default", limits)
        else:
            limits = provider_limits.get("default", limits)

        return limits


# Global token counter instance
token_counter = TokenCounter()
