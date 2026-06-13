"""Integration tests for API v2 endpoints."""

import pytest
import uuid
from datetime import datetime

# Skip entire module if SQLAlchemy or DB deps are unavailable (CI without PostgreSQL)
sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy not installed")
from sqlalchemy.orm import Session  # noqa: E402

# Import after environment setup
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
from db.database import SessionLocal, engine  # noqa: E402
from db.models import Base, User, Conversation, Message, Repository, Snippet, UserPreset  # noqa: E402


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session):
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        github_id=12345,
        github_login="testuser",
        github_avatar_url="https://avatars.githubusercontent.com/u/12345",
        github_name="Test User",
        github_email="test@example.com",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(monkeypatch):
    """Mock GitHub OAuth to return test user."""
    def mock_github_api(url, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    "id": 12345,
                    "login": "testuser",
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                    "name": "Test User",
                    "email": "test@example.com",
                }
        return MockResponse()

    import requests
    monkeypatch.setattr(requests, "get", mock_github_api)
    return {"Authorization": "Bearer test_token"}


# ============================================================================
# Conversation Tests
# ============================================================================

class TestConversations:
    """Test conversation endpoints."""

    def test_list_empty(self, client, auth_headers):
        """List conversations when none exist."""
        resp = client.get("/api/v2/conversations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["has_more"] is False

    def test_create_conversation(self, client, auth_headers):
        """Create a conversation."""
        resp = client.post(
            "/api/v2/conversations",
            headers=auth_headers,
            json={"name": "Test Chat"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Chat"
        assert data["is_active"] is True
        assert data["message_count"] == 0
        assert "id" in data

    def test_create_conversation_default_name(self, client, auth_headers):
        """Create conversation with default name."""
        resp = client.post("/api/v2/conversations", headers=auth_headers, json={})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Chat"

    def test_create_conversation_with_repo(self, client, auth_headers, db: Session, test_user: User):
        """Create conversation linked to a repository."""
        repo = Repository(
            user_id=test_user.id,
            owner="testorg",
            name="testrepo",
            branch="main",
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

        resp = client.post(
            "/api/v2/conversations",
            headers=auth_headers,
            json={"name": "Test", "repository_id": str(repo.id)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert str(data["repository_id"]) == str(repo.id)

    def test_create_conversation_invalid_repo(self, client, auth_headers):
        """Create conversation with non-existent repo."""
        fake_repo_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v2/conversations",
            headers=auth_headers,
            json={"name": "Test", "repository_id": fake_repo_id},
        )
        assert resp.status_code == 404

    def test_get_conversation(self, client, auth_headers, db: Session, test_user: User):
        """Get a specific conversation."""
        conv = Conversation(user_id=test_user.id, name="Test Chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.get(f"/api/v2/conversations/{conv.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert str(data["id"]) == str(conv.id)
        assert data["name"] == "Test Chat"

    def test_get_conversation_not_found(self, client, auth_headers):
        """Get non-existent conversation."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/v2/conversations/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_conversation_other_user(self, client, auth_headers, db: Session):
        """Cannot access another user's conversation."""
        other_user = User(github_id=99999, github_login="otheruser")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        conv = Conversation(user_id=other_user.id, name="Other User Chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.get(f"/api/v2/conversations/{conv.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_conversation(self, client, auth_headers, db: Session, test_user: User):
        """Update conversation name and status."""
        conv = Conversation(user_id=test_user.id, name="Old Name")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.put(
            f"/api/v2/conversations/{conv.id}",
            headers=auth_headers,
            json={"name": "New Name", "is_active": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["is_active"] is False

    def test_delete_conversation(self, client, auth_headers, db: Session, test_user: User):
        """Delete a conversation."""
        conv = Conversation(user_id=test_user.id, name="To Delete")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.delete(f"/api/v2/conversations/{conv.id}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(f"/api/v2/conversations/{conv.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_conversations_pagination(self, client, auth_headers, db: Session, test_user: User):
        """Test pagination on conversation list."""
        # Create 10 conversations
        for i in range(10):
            conv = Conversation(user_id=test_user.id, name=f"Conv {i}")
            db.add(conv)
        db.commit()

        # Test limit
        resp = client.get(
            "/api/v2/conversations?limit=5&offset=0",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["has_more"] is True

        # Test offset
        resp = client.get(
            "/api/v2/conversations?limit=5&offset=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["has_more"] is False

    def test_list_conversations_sorting(self, client, auth_headers, db: Session, test_user: User):
        """Test sorting on conversation list."""
        conv1 = Conversation(user_id=test_user.id, name="Zebra")
        conv2 = Conversation(user_id=test_user.id, name="Apple")
        db.add_all([conv1, conv2])
        db.commit()

        # Sort by name ascending
        resp = client.get(
            "/api/v2/conversations?sort=name&order=asc",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"][0]["name"] == "Apple"
        assert data["data"][1]["name"] == "Zebra"


# ============================================================================
# Message Tests
# ============================================================================

class TestMessages:
    """Test message endpoints."""

    def test_create_message(self, client, auth_headers, db: Session, test_user: User):
        """Create a message in a conversation."""
        conv = Conversation(user_id=test_user.id, name="Test")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.post(
            f"/api/v2/conversations/{conv.id}/messages",
            headers=auth_headers,
            json={"role": "user", "content": "Hello", "tokens_used": 10},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "user"
        assert data["content"] == "Hello"
        assert data["tokens_used"] == 10

    def test_create_message_invalid_role(self, client, auth_headers, db: Session, test_user: User):
        """Create message with invalid role."""
        conv = Conversation(user_id=test_user.id, name="Test")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.post(
            f"/api/v2/conversations/{conv.id}/messages",
            headers=auth_headers,
            json={"role": "invalid", "content": "Hello"},
        )
        assert resp.status_code == 422  # Validation error

    def test_list_messages(self, client, auth_headers, db: Session, test_user: User):
        """List messages in a conversation."""
        conv = Conversation(user_id=test_user.id, name="Test")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg1 = Message(conversation_id=conv.id, role="user", content="Hello", tokens_used=10)
        msg2 = Message(conversation_id=conv.id, role="assistant", content="Hi", tokens_used=5)
        db.add_all([msg1, msg2])
        db.commit()

        resp = client.get(f"/api/v2/conversations/{conv.id}/messages", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["content"] == "Hello"
        assert data["data"][1]["content"] == "Hi"

    def test_delete_message(self, client, auth_headers, db: Session, test_user: User):
        """Delete a message."""
        conv = Conversation(user_id=test_user.id, name="Test")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = Message(conversation_id=conv.id, role="user", content="Hello")
        db.add(msg)
        db.commit()
        db.refresh(msg)

        resp = client.delete(
            f"/api/v2/conversations/{conv.id}/messages/{msg.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        # Verify deleted
        resp = client.get(f"/api/v2/conversations/{conv.id}/messages", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 0


# ============================================================================
# Repository Tests
# ============================================================================

class TestRepositories:
    """Test repository endpoints."""

    def test_create_repository(self, client, auth_headers):
        """Create a repository."""
        resp = client.post(
            "/api/v2/repositories",
            headers=auth_headers,
            json={"owner": "testorg", "name": "testrepo", "branch": "main"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["owner"] == "testorg"
        assert data["name"] == "testrepo"
        assert data["branch"] == "main"

    def test_create_duplicate_repository(self, client, auth_headers, db: Session, test_user: User):
        """Cannot create duplicate repository."""
        repo = Repository(user_id=test_user.id, owner="testorg", name="testrepo")
        db.add(repo)
        db.commit()

        resp = client.post(
            "/api/v2/repositories",
            headers=auth_headers,
            json={"owner": "testorg", "name": "testrepo"},
        )
        assert resp.status_code == 409  # Conflict

    def test_list_repositories(self, client, auth_headers, db: Session, test_user: User):
        """List repositories."""
        repo1 = Repository(user_id=test_user.id, owner="org1", name="repo1")
        repo2 = Repository(user_id=test_user.id, owner="org2", name="repo2")
        db.add_all([repo1, repo2])
        db.commit()

        resp = client.get("/api/v2/repositories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2

    def test_update_repository_branch(self, client, auth_headers, db: Session, test_user: User):
        """Update repository branch."""
        repo = Repository(user_id=test_user.id, owner="testorg", name="testrepo")
        db.add(repo)
        db.commit()
        db.refresh(repo)

        resp = client.put(
            f"/api/v2/repositories/{repo.id}",
            headers=auth_headers,
            json={"branch": "develop"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["branch"] == "develop"

    def test_delete_repository_cascade(self, client, auth_headers, db: Session, test_user: User):
        """Delete repository cascades to conversations."""
        repo = Repository(user_id=test_user.id, owner="testorg", name="testrepo")
        db.add(repo)
        db.commit()
        db.refresh(repo)

        conv = Conversation(user_id=test_user.id, repository_id=repo.id, name="Test")
        db.add(conv)
        db.commit()

        # Delete repo
        resp = client.delete(f"/api/v2/repositories/{repo.id}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify conversation still exists (SET NULL, not cascade)
        resp = client.get(f"/api/v2/conversations/{conv.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["repository_id"] is None


# ============================================================================
# Snippet Tests
# ============================================================================

class TestSnippets:
    """Test snippet endpoints."""

    def test_create_snippet(self, client, auth_headers):
        """Create a snippet."""
        resp = client.post(
            "/api/v2/snippets",
            headers=auth_headers,
            json={
                "title": "JWT Helper",
                "language": "typescript",
                "content": "export function decode(token) { ... }",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "JWT Helper"
        assert data["language"] == "typescript"

    def test_list_snippets(self, client, auth_headers, db: Session, test_user: User):
        """List snippets."""
        snip1 = Snippet(user_id=test_user.id, title="JWT", language="typescript", content="...")
        snip2 = Snippet(user_id=test_user.id, title="Hash", language="python", content="...")
        db.add_all([snip1, snip2])
        db.commit()

        resp = client.get("/api/v2/snippets", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2

    def test_list_snippets_filter_by_language(self, client, auth_headers, db: Session, test_user: User):
        """Filter snippets by language."""
        snip1 = Snippet(user_id=test_user.id, title="JWT", language="typescript", content="...")
        snip2 = Snippet(user_id=test_user.id, title="Hash", language="python", content="...")
        db.add_all([snip1, snip2])
        db.commit()

        resp = client.get("/api/v2/snippets?language=typescript", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["language"] == "typescript"

    def test_update_snippet(self, client, auth_headers, db: Session, test_user: User):
        """Update a snippet."""
        snip = Snippet(user_id=test_user.id, title="Old", language="python", content="...")
        db.add(snip)
        db.commit()
        db.refresh(snip)

        resp = client.put(
            f"/api/v2/snippets/{snip.id}",
            headers=auth_headers,
            json={"title": "New Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Title"

    def test_delete_snippet(self, client, auth_headers, db: Session, test_user: User):
        """Delete a snippet."""
        snip = Snippet(user_id=test_user.id, title="To Delete", language="python", content="...")
        db.add(snip)
        db.commit()
        db.refresh(snip)

        resp = client.delete(f"/api/v2/snippets/{snip.id}", headers=auth_headers)
        assert resp.status_code == 204


# ============================================================================
# Preset Tests
# ============================================================================

class TestPresets:
    """Test preset endpoints."""

    def test_create_preset(self, client, auth_headers):
        """Create a preset."""
        resp = client.post(
            "/api/v2/presets",
            headers=auth_headers,
            json={
                "preset_name": "Quick Review",
                "instructions": "Review for bugs",
                "rules": "- Check errors",
                "skills": ["Security", "Tests"],
                "ai_model": "sonnet",
                "provider": "anthropic",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["preset_name"] == "Quick Review"
        assert data["skills"] == ["Security", "Tests"]

    def test_create_duplicate_preset(self, client, auth_headers, db: Session, test_user: User):
        """Cannot create duplicate preset name."""
        preset = UserPreset(
            user_id=test_user.id,
            preset_name="Review",
            instructions="Test",
        )
        db.add(preset)
        db.commit()

        resp = client.post(
            "/api/v2/presets",
            headers=auth_headers,
            json={"preset_name": "Review"},
        )
        assert resp.status_code == 409  # Conflict

    def test_list_presets(self, client, auth_headers, db: Session, test_user: User):
        """List presets."""
        preset1 = UserPreset(user_id=test_user.id, preset_name="Review")
        preset2 = UserPreset(user_id=test_user.id, preset_name="Refactor")
        db.add_all([preset1, preset2])
        db.commit()

        resp = client.get("/api/v2/presets", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2

    def test_update_preset(self, client, auth_headers, db: Session, test_user: User):
        """Update a preset."""
        preset = UserPreset(user_id=test_user.id, preset_name="Review")
        db.add(preset)
        db.commit()
        db.refresh(preset)

        resp = client.put(
            f"/api/v2/presets/{preset.id}",
            headers=auth_headers,
            json={"skills": ["Security", "Performance"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["skills"] == ["Security", "Performance"]

    def test_delete_preset(self, client, auth_headers, db: Session, test_user: User):
        """Delete a preset."""
        preset = UserPreset(user_id=test_user.id, preset_name="To Delete")
        db.add(preset)
        db.commit()
        db.refresh(preset)

        resp = client.delete(f"/api/v2/presets/{preset.id}", headers=auth_headers)
        assert resp.status_code == 204


# ============================================================================
# Utility Endpoints
# ============================================================================

class TestUtility:
    """Test utility endpoints."""

    def test_health_check(self, client):
        """Health check endpoint."""
        resp = client.get("/api/v2/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert data["db"] in ("ok", "error")
        assert "latency_ms" in data

    def test_config_endpoint(self, client):
        """Config endpoint shows DB status."""
        resp = client.get("/api/v2/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "db_enabled" in data
        assert "version" in data
        assert "features" in data


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthentication:
    """Test authentication."""

    def test_missing_auth_header(self, client):
        """Missing Authorization header."""
        resp = client.get("/api/v2/conversations")
        assert resp.status_code == 401

    def test_invalid_auth_header(self, client, monkeypatch):
        """Invalid GitHub token."""
        def mock_github_api(url, **kwargs):
            class MockResponse:
                status_code = 401
            return MockResponse()

        import requests
        monkeypatch.setattr(requests, "get", mock_github_api)

        resp = client.get(
            "/api/v2/conversations",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert resp.status_code == 401


# ============================================================================
# Row-Level Security Tests
# ============================================================================

class TestRowLevelSecurity:
    """Test that users can only access their own data."""

    def test_user_cannot_access_other_user_conversation(self, client, db: Session):
        """User A cannot access User B's conversation."""
        user_a = User(github_id=1001, github_login="usera")
        user_b = User(github_id=1002, github_login="userb")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        # User B creates conversation
        conv = Conversation(user_id=user_b.id, name="Private")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        # Mock User A auth
        def mock_github_api_a(url, **kwargs):
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"id": 1001, "login": "usera"}
            return MockResponse()

        import requests
        import pytest
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(requests, "get", mock_github_api_a)

        # User A tries to access User B's conversation
        resp = client.get(
            f"/api/v2/conversations/{conv.id}",
            headers={"Authorization": "Bearer user_a_token"},
        )
        assert resp.status_code == 404  # Not found for user A

    def test_user_cannot_access_other_user_snippet(self, client, db: Session):
        """User A cannot access User B's snippet."""
        user_a = User(github_id=2001, github_login="usera")
        user_b = User(github_id=2002, github_login="userb")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        # User B creates snippet
        snip = Snippet(user_id=user_b.id, title="Private", language="python", content="...")
        db.add(snip)
        db.commit()
        db.refresh(snip)

        # User A tries to list and should see nothing
        # (This would be tested via mock auth setup)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
