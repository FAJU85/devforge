#!/usr/bin/env python3
"""
Chat Service
Handles message processing and LLM provider routing
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import json
from api.services.config_service import config_service
from api.services.providers import ProviderFactory
from api.services.token_counter import token_counter


class Message:
    """Message model"""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class Conversation:
    """Conversation model"""

    def __init__(self, conversation_id: str):
        self.id = conversation_id
        self.messages: List[Message] = []
        self.model: str = "claude-3-5-sonnet-20241022"
        self.provider: str = "anthropic"
        self.tokens_used: int = 0
        self.total_cost: float = 0.0

    def add_message(self, role: str, content: str):
        """Add message to conversation"""
        self.messages.append(Message(role, content))

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API calls"""
        return [msg.to_dict() for msg in self.messages]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "model": self.model,
            "provider": self.provider,
            "message_count": len(self.messages),
            "tokens_used": self.tokens_used,
            "total_cost": self.total_cost,
            "messages": self.get_messages_for_api(),
        }


class ChatService:
    """Handles chat message processing and LLM provider routing"""

    def __init__(self):
        """Initialize chat service"""
        self.conversations: Dict[str, Conversation] = {}

    def create_conversation(self, conversation_id: str) -> Conversation:
        """
        Create a new conversation

        Args:
            conversation_id: Unique conversation ID

        Returns:
            Created conversation
        """
        conv = Conversation(conversation_id)
        self.conversations[conversation_id] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation or None
        """
        return self.conversations.get(conversation_id)

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> Conversation:
        """
        Add message to conversation

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Updated conversation
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            conv = self.create_conversation(conversation_id)

        conv.add_message(role, content)
        return conv

    async def process_message(
        self,
        user_id: int,
        conversation_id: str,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process user message and get LLM response

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            message: User message
            model: Optional model override
            provider: Optional provider override

        Returns:
            Response with role and content
        """
        # Get user config
        config = config_service.get_config(user_id)
        if not model:
            model = config.get("preferred_model", "claude-3-5-sonnet-20241022")
        if not provider:
            provider = config.get("preferred_provider", "anthropic")

        # Add user message to conversation
        conv = self.add_message(conversation_id, "user", message)
        conv.model = model
        conv.provider = provider

        try:
            # Get API key for provider
            api_key = config_service.get_api_key(user_id, provider)
            if not api_key:
                error_msg = f"No API key configured for {provider}. Please set up your API key in settings."
                response_content = f"[ERROR] {error_msg}"
                self.add_message(conversation_id, "assistant", response_content)
                return {
                    "role": "assistant",
                    "content": response_content,
                    "model": model,
                    "provider": provider,
                    "error": True,
                }

            # Create provider instance
            llm_provider = ProviderFactory.create_provider(provider, api_key)

            # Get conversation history for context
            messages = conv.get_messages_for_api()

            # Get user preferences
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 4096)

            # Call the LLM provider
            response = await llm_provider.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_content = response.content

            # Store token usage if available
            conv.tokens_used = response.usage.total_tokens if response.usage else 0

        except ValueError as e:
            # Provider not supported
            response_content = f"[ERROR] {str(e)}"
        except RuntimeError as e:
            # Provider error (API key, connection, etc.)
            response_content = f"[ERROR] {str(e)}"
        except Exception as e:
            # Unexpected error
            response_content = f"[ERROR] Unexpected error: {str(e)}"

        # Add assistant response to conversation
        self.add_message(conversation_id, "assistant", response_content)

        return {
            "role": "assistant",
            "content": response_content,
            "model": model,
            "provider": provider,
            "tokens_used": getattr(conv, "tokens_used", 0),
        }

    async def stream_message(
        self,
        user_id: int,
        conversation_id: str,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream message response from LLM

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            message: User message
            model: Optional model override
            provider: Optional provider override

        Yields:
            Response chunks as they arrive
        """
        # Get user config
        config = config_service.get_config(user_id)
        if not model:
            model = config.get("preferred_model", "claude-3-5-sonnet-20241022")
        if not provider:
            provider = config.get("preferred_provider", "anthropic")

        # Add user message
        conv = self.add_message(conversation_id, "user", message)
        conv.model = model
        conv.provider = provider

        try:
            # Get API key for provider
            api_key = config_service.get_api_key(user_id, provider)
            if not api_key:
                error_msg = f"No API key configured for {provider}. Please set up your API key in settings."
                yield f"[ERROR] {error_msg}"
                self.add_message(conversation_id, "assistant", error_msg)
                return

            # Create provider instance
            llm_provider = ProviderFactory.create_provider(provider, api_key)

            # Get conversation history for context
            messages = conv.get_messages_for_api()

            # Get user preferences
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 4096)

            # Collect full response while streaming
            full_response = ""

            # Stream from the provider
            async for chunk in llm_provider.stream_generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                full_response += chunk
                yield chunk

            # Add full response to conversation
            if full_response:
                self.add_message(conversation_id, "assistant", full_response)

        except ValueError as e:
            # Provider not supported
            error_msg = str(e)
            yield f"[ERROR] {error_msg}"
            self.add_message(conversation_id, "assistant", error_msg)
        except RuntimeError as e:
            # Provider error (API key, connection, etc.)
            error_msg = str(e)
            yield f"[ERROR] {error_msg}"
            self.add_message(conversation_id, "assistant", error_msg)
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {str(e)}"
            yield f"[ERROR] {error_msg}"
            self.add_message(conversation_id, "assistant", error_msg)

    def list_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List conversations for user (placeholder)

        Args:
            user_id: User ID

        Returns:
            List of conversation summaries
        """
        return [
            conv.to_dict() for conv in self.conversations.values()
        ]

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False


# Global chat service instance
chat_service = ChatService()
