"""Phase 6 Integration Tests - Database, Rate Limiting, Logging, Deployment"""

import pytest
from datetime import datetime
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Test database with SQLite
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database"""
    from db.models import Base
    
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    yield SessionLocal()
    
    Base.metadata.drop_all(bind=engine)


class TestDatabaseService:
    """Phase 6.2: Database Service Tests"""

    def test_init_db(self):
        """Test database initialization"""
        from api.services.database_service import DatabaseService
        
        # Should not raise exception
        assert DatabaseService.init_db() == True

    def test_health_check(self):
        """Test database health check"""
        from api.services.database_service import DatabaseService
        
        health = DatabaseService.health_check()
        assert health["status"] == "healthy"
        assert "database" in health

    def test_repository_create(self, test_db):
        """Test RepositoryBase.create()"""
        from api.services.database_service import RepositoryBase
        from db.models import User
        
        repo = RepositoryBase(User)
        user = repo.create(test_db, github_id=123, github_login="testuser")
        
        assert user.id is not None
        assert user.github_id == 123
        assert user.github_login == "testuser"
        assert user.is_deleted == False

    def test_repository_read(self, test_db):
        """Test RepositoryBase.read()"""
        from api.services.database_service import RepositoryBase
        from db.models import User
        
        repo = RepositoryBase(User)
        user = repo.create(test_db, github_id=456, github_login="testuser2")
        
        retrieved = repo.read(test_db, user.id)
        assert retrieved is not None
        assert retrieved.github_id == 456

    def test_repository_update(self, test_db):
        """Test RepositoryBase.update()"""
        from api.services.database_service import RepositoryBase
        from db.models import User
        
        repo = RepositoryBase(User)
        user = repo.create(test_db, github_id=789, github_login="testuser3")
        
        updated = repo.update(test_db, user.id, github_name="Test User")
        assert updated.github_name == "Test User"
        assert updated.version == 2

    def test_repository_soft_delete(self, test_db):
        """Test soft delete functionality"""
        from api.services.database_service import RepositoryBase
        from db.models import User
        
        repo = RepositoryBase(User)
        user = repo.create(test_db, github_id=999, github_login="testdelete")
        
        repo.delete(test_db, user.id)
        
        # Soft delete - record still exists but marked deleted
        retrieved = test_db.query(User).filter(User.id == user.id).first()
        assert retrieved.is_deleted == True
        assert retrieved.deleted_at is not None

    def test_repository_list(self, test_db):
        """Test RepositoryBase.list()"""
        from api.services.database_service import RepositoryBase
        from db.models import User
        
        repo = RepositoryBase(User)
        
        # Create multiple users
        for i in range(5):
            repo.create(test_db, github_id=1000+i, github_login=f"user{i}")
        
        users = repo.list(test_db, limit=10)
        assert len(users) == 5


class TestAuditService:
    """Phase 6.4: Audit Service Tests"""

    def test_log_action(self, test_db):
        """Test audit logging"""
        from api.services.audit_service import AuditService
        from db.models import ActionEnum
        from uuid import uuid4
        
        service = AuditService()
        user_id = uuid4()
        
        result = service.log_action(
            user_id=user_id,
            entity_type="Config",
            entity_id="test_config",
            action=ActionEnum.CONFIG_CHANGE,
            changes={"theme": "light"},
            reason="User preference"
        )
        
        assert result == True

    def test_log_config_change(self, test_db):
        """Test config change logging"""
        from api.services.audit_service import AuditService
        from uuid import uuid4
        
        service = AuditService()
        user_id = uuid4()
        
        result = service.log_config_change(
            user_id=user_id,
            config_key="theme",
            old_value="light",
            new_value="dark",
            reason="User preference change"
        )
        
        assert result == True

    def test_log_api_key_access(self, test_db):
        """Test API key access logging"""
        from api.services.audit_service import AuditService
        from uuid import uuid4
        
        service = AuditService()
        user_id = uuid4()
        
        result = service.log_api_key_access(
            user_id=user_id,
            provider="anthropic",
            action="rotated"
        )
        
        assert result == True

    def test_log_task_execution(self, test_db):
        """Test task execution logging"""
        from api.services.audit_service import AuditService
        from uuid import uuid4
        
        service = AuditService()
        user_id = uuid4()
        task_id = uuid4()
        
        result = service.log_task_execution(
            user_id=user_id,
            task_id=task_id,
            status="completed",
            result={"lines_processed": 100}
        )
        
        assert result == True


class TestRateLimiter:
    """Phase 6.3: Rate Limiting Tests"""

    def test_global_rate_limit(self):
        """Test global rate limiting"""
        from api.security import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=5)
        user_id = "test_user"
        
        # Should allow first 5 requests
        for i in range(5):
            assert limiter.is_allowed(user_id) == True
        
        # 6th request should be denied
        assert limiter.is_allowed(user_id) == False

    def test_retry_after(self):
        """Test retry-after calculation"""
        from api.security import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=2)
        user_id = "test_user"
        
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        
        # Should be limited
        assert limiter.is_allowed(user_id) == False
        
        # Get retry after
        retry_after = limiter.get_retry_after(user_id)
        assert retry_after > 0
        assert retry_after <= 60


class TestMonitoring:
    """Phase 6.4: Monitoring Tests"""

    def test_event_logger(self):
        """Test event logging"""
        from api.monitoring import EventLogger, EventLevel
        
        logger = EventLogger("test")
        
        logger.log_event(
            "test_event",
            EventLevel.INFO,
            "Test message",
            {"key": "value"}
        )
        
        events = logger.get_recent_events(limit=10)
        assert len(events) > 0
        assert events[-1]["message"] == "Test message"

    def test_metrics_collector(self):
        """Test metrics collection"""
        from api.monitoring import MetricsCollector
        
        metrics = MetricsCollector()
        
        # Test counters
        metrics.increment_counter("requests", 5)
        metrics.increment_counter("requests", 3)
        
        stats = metrics.get_stats()
        assert stats["counters"]["requests"] == 8

    def test_performance_monitor(self):
        """Test performance monitoring"""
        from api.monitoring import PerformanceMonitor, MetricsCollector, EventLogger
        import time
        
        metrics = MetricsCollector()
        logger = EventLogger("test")
        monitor = PerformanceMonitor(metrics, logger)
        
        # Measure operation
        with monitor.measure_operation("test_op"):
            time.sleep(0.1)
        
        stats = metrics.get_stats()
        assert "test_op" in stats["timers"]
        assert stats["timers"]["test_op"]["count"] == 1


class TestModels:
    """Phase 6.2: Model Tests"""

    def test_user_model(self, test_db):
        """Test User model"""
        from db.models import User
        
        user = User(
            github_id=12345,
            github_login="testuser",
            github_name="Test User"
        )
        
        test_db.add(user)
        test_db.commit()
        
        retrieved = test_db.query(User).filter(User.github_id == 12345).first()
        assert retrieved.github_login == "testuser"
        assert retrieved.version == 1

    def test_conversation_model(self, test_db):
        """Test Conversation model"""
        from db.models import User, Conversation
        
        user = User(github_id=123, github_login="user1")
        test_db.add(user)
        test_db.commit()
        
        conv = Conversation(user_id=user.id, name="Test Chat")
        test_db.add(conv)
        test_db.commit()
        
        retrieved = test_db.query(Conversation).filter(Conversation.user_id == user.id).first()
        assert retrieved.name == "Test Chat"
        assert retrieved.version == 1

    def test_audit_log_model(self, test_db):
        """Test AuditLog model"""
        from db.models import User, AuditLog, ActionEnum
        
        user = User(github_id=456, github_login="user2")
        test_db.add(user)
        test_db.commit()
        
        audit = AuditLog(
            user_id=user.id,
            entity_type="Config",
            entity_id="test_config",
            action=ActionEnum.CONFIG_CHANGE,
            changes={"theme": "dark"}
        )
        test_db.add(audit)
        test_db.commit()
        
        retrieved = test_db.query(AuditLog).filter(AuditLog.user_id == user.id).first()
        assert retrieved.action == ActionEnum.CONFIG_CHANGE


class TestDeployment:
    """Phase 6.5: Deployment Tests"""

    def test_entrypoint_exists(self):
        """Test entrypoint script exists"""
        assert os.path.exists("/home/user/devforge/scripts/entrypoint.sh")

    def test_deploy_script_exists(self):
        """Test deploy script exists"""
        assert os.path.exists("/home/user/devforge/scripts/deploy.sh")

    def test_dockerfile_exists(self):
        """Test Dockerfile exists"""
        assert os.path.exists("/home/user/devforge/Dockerfile.api")

    def test_docker_compose_config(self):
        """Test docker-compose configuration"""
        import yaml
        
        with open("/home/user/devforge/docker-compose.prod.yml", "r") as f:
            config = yaml.safe_load(f)
        
        assert "services" in config
        assert "fastapi-backend" in config["services"]
        assert "postgres" in config["services"]
        assert "redis" in config["services"]

    def test_env_example_exists(self):
        """Test environment example exists"""
        assert os.path.exists("/home/user/devforge/.env.example")

    def test_logging_config_exists(self):
        """Test logging configuration exists"""
        assert os.path.exists("/home/user/devforge/config/logging.json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
