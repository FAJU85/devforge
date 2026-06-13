"""DevForge API v2 Schemas - Request/Response models for database-backed endpoints."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ============================================================================
# Configuration
# ============================================================================

class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class PaginationResponse(BaseModel):
    limit: int
    offset: int
    total: int
    has_more: bool


# ============================================================================
# Conversations
# ============================================================================

class ConversationCreate(BaseModel):
    name: str = Field(default="Chat", max_length=255)
    repository_id: Optional[UUID] = None
    model_config = ConfigDict(json_schema_extra={"example": {"name": "Frontend Refactor"}})


class ConversationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class ConversationResponse(BaseModel):
    id: UUID
    name: str
    repository_id: Optional[UUID]
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationsListResponse(BaseModel):
    data: List[ConversationResponse]
    pagination: PaginationResponse


# ============================================================================
# Messages
# ============================================================================

class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=100000)
    tokens_used: int = Field(default=0, ge=0)
    model_config = ConfigDict(json_schema_extra={"example": {"role": "user", "content": "Fix the login button", "tokens_used": 150}})


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tokens_used: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MessagesListResponse(BaseModel):
    data: List[MessageResponse]
    pagination: PaginationResponse


# ============================================================================
# Repositories
# ============================================================================

class RepositoryCreate(BaseModel):
    owner: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    branch: str = Field(default="main", max_length=255)
    model_config = ConfigDict(json_schema_extra={"example": {"owner": "faju85", "name": "devforge"}})


class RepositoryUpdate(BaseModel):
    branch: Optional[str] = Field(None, max_length=255)
    last_accessed: Optional[datetime] = None


class RepositoryResponse(BaseModel):
    id: UUID
    owner: str
    name: str
    branch: str
    last_accessed: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RepositoriesListResponse(BaseModel):
    data: List[RepositoryResponse]
    pagination: PaginationResponse


# ============================================================================
# Snippets
# ============================================================================

class SnippetCreate(BaseModel):
    title: str = Field(..., max_length=255)
    language: Optional[str] = Field(None, max_length=50)
    content: str = Field(..., max_length=1000000)
    model_config = ConfigDict(json_schema_extra={"example": {"title": "JWT Helper", "language": "typescript", "content": "export function decode(token) { ... }"}})


class SnippetUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, max_length=50)
    content: Optional[str] = Field(None, max_length=1000000)


class SnippetResponse(BaseModel):
    id: UUID
    title: str
    language: Optional[str]
    content: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SnippetsListResponse(BaseModel):
    data: List[SnippetResponse]
    pagination: PaginationResponse


# ============================================================================
# Presets
# ============================================================================

class PresetCreate(BaseModel):
    preset_name: str = Field(..., max_length=255)
    instructions: Optional[str] = None
    rules: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    ai_model: Optional[str] = Field(None, max_length=255)
    provider: Optional[str] = Field(None, max_length=50)
    model_config = ConfigDict(json_schema_extra={"example": {"preset_name": "Quick Review", "skills": ["Security", "Tests"], "ai_model": "sonnet", "provider": "anthropic"}})


class PresetUpdate(BaseModel):
    preset_name: Optional[str] = Field(None, max_length=255)
    instructions: Optional[str] = None
    rules: Optional[str] = None
    skills: Optional[List[str]] = None
    ai_model: Optional[str] = Field(None, max_length=255)
    provider: Optional[str] = Field(None, max_length=50)


class PresetResponse(BaseModel):
    id: UUID
    preset_name: str
    instructions: Optional[str]
    rules: Optional[str]
    skills: List[str]
    ai_model: Optional[str]
    provider: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PresetsListResponse(BaseModel):
    data: List[PresetResponse]
    pagination: PaginationResponse


# ============================================================================
# Secrets (Encrypted API Keys)
# ============================================================================

class SecretCreate(BaseModel):
    secret_type: str = Field(..., max_length=50)
    secret_value: str = Field(..., max_length=10000)
    model_config = ConfigDict(json_schema_extra={"example": {"secret_type": "anthropic_key", "secret_value": "sk-ant-..."}})


class SecretResponse(BaseModel):
    secret_type: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Error Response
# ============================================================================

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    error: dict = Field(default_factory=dict)
    model_config = ConfigDict(json_schema_extra={"example": {"error": {"code": "VALIDATION_ERROR", "message": "Invalid request body", "details": [{"field": "name", "message": "must be at most 255 characters"}]}}})


# ============================================================================
# Config & Health
# ============================================================================

class ConfigResponse(BaseModel):
    db_enabled: bool
    version: str
    features: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    db: str
    latency_ms: int
