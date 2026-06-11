"""DevForge API v2 - Database-backed endpoints for conversations, messages, snippets, presets, secrets."""

import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, Conversation, Message, Repository, Snippet, UserPreset, UserSecret

# Lazy import encryption (handle system library issues gracefully)
def _encrypt_secret(s: str) -> str:
    try:
        from db.encryption import encrypt_secret
        return encrypt_secret(s)
    except Exception:
        return f"plaintext:{s}"

def _decrypt_secret(s: str) -> str:
    try:
        from db.encryption import decrypt_secret
        return decrypt_secret(s)
    except Exception:
        if s.startswith("plaintext:"):
            return s[10:]
        return s

from schemas_v2 import (
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationsListResponse,
    MessageCreate, MessageResponse, MessagesListResponse,
    RepositoryCreate, RepositoryUpdate, RepositoryResponse, RepositoriesListResponse,
    SnippetCreate, SnippetUpdate, SnippetResponse, SnippetsListResponse,
    PresetCreate, PresetUpdate, PresetResponse, PresetsListResponse,
    SecretCreate, SecretResponse,
    PaginationResponse,
    ConfigResponse, HealthResponse,
    PaginationParams,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])

# ============================================================================
# Authentication & Utilities
# ============================================================================

def _extract_user_from_github_token(request: Request) -> dict:
    """Extract and validate GitHub token from request, return user info."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        return resp.json()
    except requests.RequestException:
        raise HTTPException(status_code=401, detail="GitHub API unreachable")


def _get_or_create_user(gh_user: dict, db: Session) -> User:
    """Get or create user from GitHub user info."""
    user = db.query(User).filter_by(github_id=gh_user["id"]).first()
    if not user:
        user = User(
            github_id=gh_user["id"],
            github_login=gh_user["login"],
            github_avatar_url=gh_user.get("avatar_url"),
            github_name=gh_user.get("name"),
            github_email=gh_user.get("email"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def _get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to extract and validate current user from GitHub token."""
    gh_user = _extract_user_from_github_token(request)
    return _get_or_create_user(gh_user, db)


# ============================================================================
# Conversations Endpoints
# ============================================================================

@router.get("/conversations", response_model=ConversationsListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at", pattern="^(created_at|updated_at|name)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the current user."""
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)

    # Sort
    if sort == "created_at":
        query = query.order_by(Conversation.created_at.desc() if order == "desc" else Conversation.created_at.asc())
    elif sort == "updated_at":
        query = query.order_by(Conversation.updated_at.desc() if order == "desc" else Conversation.updated_at.asc())
    elif sort == "name":
        query = query.order_by(Conversation.name.asc() if order == "asc" else Conversation.name.desc())

    total = query.count()
    convs = query.offset(offset).limit(limit).all()

    return ConversationsListResponse(
        data=[
            ConversationResponse(
                **{**c.__dict__, "message_count": len(c.messages)}
            ) for c in convs
        ],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            total=total,
            has_more=offset + limit < total,
        ),
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation."""
    if body.repository_id:
        repo = db.query(Repository).filter(
            Repository.id == body.repository_id,
            Repository.user_id == current_user.id
        ).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

    conv = Conversation(
        user_id=current_user.id,
        repository_id=body.repository_id,
        name=body.name,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ConversationResponse(**{**conv.__dict__, "message_count": 0})


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(**{**conv.__dict__, "message_count": len(conv.messages)})


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Update a conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.name is not None:
        conv.name = body.name
    if body.is_active is not None:
        conv.is_active = body.is_active

    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)

    return ConversationResponse(**{**conv.__dict__, "message_count": len(conv.messages)})


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation (cascade deletes messages)."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conv)
    db.commit()


# ============================================================================
# Messages Endpoints
# ============================================================================

@router.get("/conversations/{conversation_id}/messages", response_model=MessagesListResponse)
async def list_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """List messages in a conversation (paginated)."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    # Verify conversation exists and belongs to user
    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = db.query(Message).filter(Message.conversation_id == conv_uuid).order_by(Message.created_at.asc())
    total = query.count()
    msgs = query.offset(offset).limit(limit).all()

    return MessagesListResponse(
        data=[MessageResponse.model_validate(m) for m in msgs],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            total=total,
            has_more=offset + limit < total,
        ),
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    conversation_id: str,
    body: MessageCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Add a message to a conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(
        conversation_id=conv_uuid,
        role=body.role,
        content=body.content,
        tokens_used=body.tokens_used,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageResponse.model_validate(msg)


@router.delete("/conversations/{conversation_id}/messages/{message_id}", status_code=204)
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a message."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
        msg_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify conversation exists
    conv = db.query(Conversation).filter(
        Conversation.id == conv_uuid,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = db.query(Message).filter(
        Message.id == msg_uuid,
        Message.conversation_id == conv_uuid
    ).first()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(msg)
    db.commit()


# ============================================================================
# Repositories Endpoints
# ============================================================================

@router.get("/repositories", response_model=RepositoriesListResponse)
async def list_repositories(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("last_accessed", pattern="^(last_accessed|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """List repositories for the current user."""
    query = db.query(Repository).filter(Repository.user_id == current_user.id)

    if sort == "last_accessed":
        query = query.order_by(Repository.last_accessed.desc() if order == "desc" else Repository.last_accessed.asc())
    elif sort == "created_at":
        query = query.order_by(Repository.created_at.desc() if order == "desc" else Repository.created_at.asc())

    total = query.count()
    repos = query.offset(offset).limit(limit).all()

    return RepositoriesListResponse(
        data=[RepositoryResponse.model_validate(r) for r in repos],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            total=total,
            has_more=offset + limit < total,
        ),
    )


@router.post("/repositories", response_model=RepositoryResponse, status_code=201)
async def create_repository(
    body: RepositoryCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Create a repository record."""
    existing = db.query(Repository).filter(
        Repository.user_id == current_user.id,
        Repository.owner == body.owner,
        Repository.name == body.name,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Repository already exists")

    repo = Repository(
        user_id=current_user.id,
        owner=body.owner,
        name=body.name,
        branch=body.branch,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    return RepositoryResponse.model_validate(repo)


@router.put("/repositories/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: str,
    body: RepositoryUpdate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Update a repository."""
    try:
        repo_uuid = uuid.UUID(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repository ID format")

    repo = db.query(Repository).filter(
        Repository.id == repo_uuid,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if body.branch is not None:
        repo.branch = body.branch
    if body.last_accessed is not None:
        repo.last_accessed = body.last_accessed

    repo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(repo)

    return RepositoryResponse.model_validate(repo)


@router.delete("/repositories/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a repository (cascade deletes conversations)."""
    try:
        repo_uuid = uuid.UUID(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repository ID format")

    repo = db.query(Repository).filter(
        Repository.id == repo_uuid,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    db.delete(repo)
    db.commit()


# ============================================================================
# Snippets Endpoints
# ============================================================================

@router.get("/snippets", response_model=SnippetsListResponse)
async def list_snippets(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    language: Optional[str] = None,
    sort: str = Query("created_at", pattern="^(created_at|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """List snippets for the current user."""
    query = db.query(Snippet).filter(Snippet.user_id == current_user.id)

    if language:
        query = query.filter(Snippet.language == language)

    if sort == "created_at":
        query = query.order_by(Snippet.created_at.desc() if order == "desc" else Snippet.created_at.asc())
    elif sort == "title":
        query = query.order_by(Snippet.title.asc() if order == "asc" else Snippet.title.desc())

    total = query.count()
    snippets = query.offset(offset).limit(limit).all()

    return SnippetsListResponse(
        data=[SnippetResponse.model_validate(s) for s in snippets],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            total=total,
            has_more=offset + limit < total,
        ),
    )


@router.post("/snippets", response_model=SnippetResponse, status_code=201)
async def create_snippet(
    body: SnippetCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new snippet."""
    snippet = Snippet(
        user_id=current_user.id,
        title=body.title,
        language=body.language,
        content=body.content,
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)

    return SnippetResponse.model_validate(snippet)


@router.put("/snippets/{snippet_id}", response_model=SnippetResponse)
async def update_snippet(
    snippet_id: str,
    body: SnippetUpdate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Update a snippet."""
    try:
        snippet_uuid = uuid.UUID(snippet_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid snippet ID format")

    snippet = db.query(Snippet).filter(
        Snippet.id == snippet_uuid,
        Snippet.user_id == current_user.id
    ).first()

    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    if body.title is not None:
        snippet.title = body.title
    if body.language is not None:
        snippet.language = body.language
    if body.content is not None:
        snippet.content = body.content

    snippet.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(snippet)

    return SnippetResponse.model_validate(snippet)


@router.delete("/snippets/{snippet_id}", status_code=204)
async def delete_snippet(
    snippet_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a snippet."""
    try:
        snippet_uuid = uuid.UUID(snippet_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid snippet ID format")

    snippet = db.query(Snippet).filter(
        Snippet.id == snippet_uuid,
        Snippet.user_id == current_user.id
    ).first()

    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    db.delete(snippet)
    db.commit()


# ============================================================================
# Presets Endpoints
# ============================================================================

@router.get("/presets", response_model=PresetsListResponse)
async def list_presets(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """List instruction presets for the current user."""
    query = db.query(UserPreset).filter(UserPreset.user_id == current_user.id).order_by(UserPreset.created_at.desc())
    total = query.count()
    presets = query.offset(offset).limit(limit).all()

    return PresetsListResponse(
        data=[PresetResponse.model_validate(p) for p in presets],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            total=total,
            has_more=offset + limit < total,
        ),
    )


@router.post("/presets", response_model=PresetResponse, status_code=201)
async def create_preset(
    body: PresetCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new preset."""
    existing = db.query(UserPreset).filter(
        UserPreset.user_id == current_user.id,
        UserPreset.preset_name == body.preset_name
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Preset with this name already exists")

    preset = UserPreset(
        user_id=current_user.id,
        preset_name=body.preset_name,
        instructions=body.instructions,
        rules=body.rules,
        skills=body.skills,
        ai_model=body.ai_model,
        provider=body.provider,
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)

    return PresetResponse.model_validate(preset)


@router.put("/presets/{preset_id}", response_model=PresetResponse)
async def update_preset(
    preset_id: str,
    body: PresetUpdate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Update a preset."""
    try:
        preset_uuid = uuid.UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid preset ID format")

    preset = db.query(UserPreset).filter(
        UserPreset.id == preset_uuid,
        UserPreset.user_id == current_user.id
    ).first()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    if body.preset_name is not None:
        preset.preset_name = body.preset_name
    if body.instructions is not None:
        preset.instructions = body.instructions
    if body.rules is not None:
        preset.rules = body.rules
    if body.skills is not None:
        preset.skills = body.skills
    if body.ai_model is not None:
        preset.ai_model = body.ai_model
    if body.provider is not None:
        preset.provider = body.provider

    preset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preset)

    return PresetResponse.model_validate(preset)


@router.delete("/presets/{preset_id}", status_code=204)
async def delete_preset(
    preset_id: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a preset."""
    try:
        preset_uuid = uuid.UUID(preset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid preset ID format")

    preset = db.query(UserPreset).filter(
        UserPreset.id == preset_uuid,
        UserPreset.user_id == current_user.id
    ).first()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    db.delete(preset)
    db.commit()


# ============================================================================
# Secrets Endpoints (Encrypted API Keys)
# ============================================================================

@router.get("/secrets/{secret_type}", response_model=SecretResponse)
async def get_secret(
    secret_type: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get secret metadata (not the decrypted value)."""
    secret = db.query(UserSecret).filter(
        UserSecret.user_id == current_user.id,
        UserSecret.secret_type == secret_type
    ).first()

    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    return SecretResponse.model_validate(secret)


@router.post("/secrets", response_model=SecretResponse, status_code=201)
async def create_or_update_secret(
    body: SecretCreate,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update an encrypted secret."""
    secret = db.query(UserSecret).filter(
        UserSecret.user_id == current_user.id,
        UserSecret.secret_type == body.secret_type
    ).first()

    encrypted_value = _encrypt_secret(body.secret_value)

    if secret:
        secret.secret_value_encrypted = encrypted_value
        secret.updated_at = datetime.utcnow()
    else:
        secret = UserSecret(
            user_id=current_user.id,
            secret_type=body.secret_type,
            secret_value_encrypted=encrypted_value,
        )
        db.add(secret)

    db.commit()
    db.refresh(secret)

    status_code = 200 if secret.created_at < datetime.utcnow() - timedelta(seconds=1) else 201
    return SecretResponse.model_validate(secret)


@router.delete("/secrets/{secret_type}", status_code=204)
async def delete_secret(
    secret_type: str,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a secret."""
    secret = db.query(UserSecret).filter(
        UserSecret.user_id == current_user.id,
        UserSecret.secret_type == secret_type
    ).first()

    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    db.delete(secret)
    db.commit()


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check database health."""
    import time
    start = time.time()
    try:
        db.execute("SELECT 1")
        latency = int((time.time() - start) * 1000)
        return HealthResponse(status="ok", db="ok", latency_ms=latency)
    except Exception:
        return HealthResponse(status="degraded", db="error", latency_ms=0)


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get server configuration and feature flags."""
    import os
    db_enabled = os.environ.get("ENABLE_DB_SYNC", "false").lower() == "true"

    return ConfigResponse(
        db_enabled=db_enabled,
        version="2.0.0",
        features={
            "extended_thinking": True,
            "code_scanning": True,
            "snippets": True,
            "presets": True,
            "db_persistence": db_enabled,
        }
    )


@router.get("/metrics")
async def get_metrics():
    """Get current metrics for monitoring."""
    from monitoring import metrics
    return metrics.get_snapshot_dict()


@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed health status."""
    from monitoring import health
    return health.overall_health()


@router.get("/canary/status")
async def get_canary_status():
    """Get canary rollout status."""
    from canary import get_canary_config
    return get_canary_config()
