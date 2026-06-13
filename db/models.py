"""DevForge Database Models (SQLAlchemy ORM)"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Text, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """GitHub OAuth authenticated user."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    github_login = Column(String(255), unique=True, nullable=False)
    github_avatar_url = Column(Text, nullable=True)
    github_name = Column(String(255), nullable=True)
    github_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    snippets = relationship("Snippet", back_populates="user", cascade="all, delete-orphan")
    presets = relationship("UserPreset", back_populates="user", cascade="all, delete-orphan")
    secrets = relationship("UserSecret", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class Repository(Base):
    """GitHub repository the user has connected."""
    __tablename__ = "repositories"
    __table_args__ = (
        Index("ix_repositories_user_id_owner_name", "user_id", "owner", "name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    branch = Column(String(255), default="main", nullable=False)
    last_accessed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="repositories")
    conversations = relationship("Conversation", back_populates="repository")


class Conversation(Base):
    """Chat conversation (tab in UI)."""
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_user_id_created_at", "user_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), default="Chat", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    repository = relationship("Repository", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    files = relationship("ConversationFile", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Chat message in a conversation."""
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class ConversationFile(Base):
    """File selected in a conversation for context."""
    __tablename__ = "conversation_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="files")


class Snippet(Base):
    """User's saved code snippet."""
    __tablename__ = "snippets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    language = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="snippets")


class UserPreset(Base):
    """User's instruction preset (rules + skills + config)."""
    __tablename__ = "user_presets"
    __table_args__ = (
        Index("ix_user_presets_user_id_name", "user_id", "preset_name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preset_name = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    skills = Column(JSON, default=list, nullable=False)  # Array of skill names
    ai_model = Column(String(255), nullable=True)  # e.g., 'haiku', 'sonnet', 'opus'
    provider = Column(String(50), nullable=True)  # 'anthropic', 'groq', 'hf', etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="presets")


class UserSecret(Base):
    """Encrypted API keys and secrets."""
    __tablename__ = "user_secrets"
    __table_args__ = (
        Index("ix_user_secrets_user_id_type", "user_id", "secret_type", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    secret_type = Column(String(50), nullable=False)  # 'anthropic_key', 'groq_key', 'hf_token', etc.
    secret_value_encrypted = Column(String(2048), nullable=False)  # Fernet-encrypted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="secrets")


class UserSession(Base):
    """User API session tokens (optional, for token-based auth)."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
