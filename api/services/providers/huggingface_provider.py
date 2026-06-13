#!/usr/bin/env python3
"""
Hugging Face Provider Implementation
Handles Hugging Face Inference API integration
"""

from typing import Dict, List, AsyncIterator, Optional
from api.services.providers.base import BaseProvider, ProviderResponse, MessageUsage
import httpx
import asyncio
import json

# Try to import transformers for tokenization
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class HuggingFaceProvider(BaseProvider):
    """Hugging Face Inference API provider implementation"""

    # Model information
    SUPPORTED_MODELS = [
        "mistralai/Mistral-7B-Instruct-v0.1",
        "meta-llama/Llama-2-7b-chat-hf",
        "meta-llama/Llama-2-13b-chat-hf",
        "meta-llama/Llama-2-70b-chat-hf",
        "tiiuae/falcon-7b-instruct",
    ]

    HF_API_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, api_key: str):
        """Initialize Hugging Face provider"""
        super().__init__(api_key)
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=self.config.timeout,
        )
        self.tokenizer = None

    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return "huggingface"

    @property
    def supported_models(self) -> List[str]:
        """Get supported models"""
        return self.SUPPORTED_MODELS

    def _get_tokenizer(self, model: str):
        """Get or load tokenizer for model"""
        if TRANSFORMERS_AVAILABLE:
            try:
                return AutoTokenizer.from_pretrained(model)
            except Exception:
                return None
        return None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> ProviderResponse:
        """
        Generate a response using Hugging Face

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            ProviderResponse with content and usage
        """
        try:
            # Format messages as a single prompt
            prompt = self._format_messages_for_hf(messages)

            # Extract parameters
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            top_p = kwargs.get("top_p", self.config.top_p)

            # Call Hugging Face API
            url = f"{self.HF_API_URL}/{model}"

            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "top_p": top_p,
                    "return_full_text": False,
                },
            }

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "")
            else:
                content = result.get("generated_text", "")

            # Estimate token usage
            input_tokens = self.count_tokens(prompt, model)
            output_tokens = self.count_tokens(content, model)

            usage = MessageUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

            return ProviderResponse(
                content=content,
                usage=usage,
                model=model,
                provider=self.provider_name,
                stop_reason="end_of_sequence",
            )

        except Exception as error:
            raise RuntimeError(f"Hugging Face API error: {self.handle_error(error)}")

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a response from Hugging Face

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        try:
            # Note: HF Inference API doesn't support streaming in the same way
            # So we'll generate the full response and yield it in chunks
            prompt = self._format_messages_for_hf(messages)

            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            top_p = kwargs.get("top_p", self.config.top_p)

            url = f"{self.HF_API_URL}/{model}"

            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "top_p": top_p,
                    "return_full_text": False,
                },
            }

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "")
            else:
                content = result.get("generated_text", "")

            # Yield in chunks (simulate streaming)
            for word in content.split():
                yield word + " "
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)

        except Exception as error:
            error_msg = self.handle_error(error)
            yield f"[ERROR] {error_msg}"

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens using tokenizer

        Args:
            text: Text to count
            model: Model to use for tokenizer

        Returns:
            Number of tokens
        """
        try:
            if TRANSFORMERS_AVAILABLE and model:
                tokenizer = self._get_tokenizer(model)
                if tokenizer:
                    tokens = tokenizer.encode(text)
                    return len(tokens)

            # Fallback to character-based estimation
            # Most tokenizers use roughly 1 token per 4 characters
            return max(1, len(text) // 4)

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
            # Format as prompt and count
            prompt = self._format_messages_for_hf(messages)
            return self.count_tokens(prompt, model)

        except Exception:
            # Fallback
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return max(1, total_chars // 4)

    def _format_messages_for_hf(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for Hugging Face prompt format

        Args:
            messages: List of messages

        Returns:
            Formatted prompt string
        """
        prompt = ""
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "system":
                prompt += f"[SYSTEM] {content}\n\n"
            elif role == "user":
                prompt += f"[USER] {content}\n"
            elif role == "assistant":
                prompt += f"[ASSISTANT] {content}\n"
            else:
                prompt += f"{content}\n"

        prompt += "[ASSISTANT]"
        return prompt

    async def validate_connection(self) -> bool:
        """
        Validate Hugging Face API connection

        Returns:
            True if connection is valid
        """
        try:
            # Try a simple API call to validate the key
            test_url = f"{self.HF_API_URL}/gpt2"  # Use a popular model for testing
            payload = {
                "inputs": "test",
                "parameters": {"max_new_tokens": 10},
            }

            response = await self.http_client.post(test_url, json=payload)
            return response.status_code in [200, 503]  # 503 is model loading

        except Exception:
            return False
