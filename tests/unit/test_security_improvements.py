"""
Comprehensive unit tests for security improvements.
Tests for fail-closed policy, rate limiting, and audit logging.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Import security components
from core.security.access_control import require_permission, require_role, set_security_service, get_security_service
from core.security.security_service import SecurityService, Permission, UserRole
from core.security.security_exceptions import SecurityServiceNotInitializedError
from core.services.rate_limiter import RateLimiter
from core.services.audit_logger import AuditLogger
from database.models import LoginAttempt, AuditLog

pytestmark = pytest.mark.unit


class TestFailClosedPolicy:
    """Tests for fail-closed security policy."""
    
    def setup_method(self):
        # Asegurar que no hay servicio global
        from core.security import access_control
        access_control.set_security_service(None)
        self.old_allow = access_control._allow_permissive_mock
        access_control._allow_permissive_mock = False

    def teardown_method(self):
        from core.security import access_control
        access_control._allow_permissive_mock = self.old_allow

    def test_require_permission_without_security_service(self):

        """Verify that @require_permission raises SecurityServiceNotInitializedError when service not initialized."""
        # Clear security service
        set_security_service(None)
        
        @require_permission(Permission.CREATE_PRODUCT)
        def protected_function():
            return "Success"
        
        # Should raise SecurityServiceNotInitializedError
        with pytest.raises(SecurityServiceNotInitializedError) as exc_info:
            protected_function()
        
        assert "SecurityService not initialized" in str(exc_info.value)
        assert "protected_function" in str(exc_info.value)
    
    def test_require_role_without_security_service(self):
        """Verify that @require_role raises SecurityServiceNotInitializedError when service not initialized."""
        set_security_service(None)
        
        @require_role(UserRole.ADMIN)
        def protected_function():
            return "Success"
        
        with pytest.raises(SecurityServiceNotInitializedError) as exc_info:
            protected_function()
        assert exc_info.type is SecurityServiceNotInitializedError
    
    def test_require_permission_with_security_service(self):
        """Verify decorators work normally when SecurityService is initialized."""
        # Create mock security service
        mock_service = Mock(spec=SecurityService)
        mock_service.has_permission.return_value = True
        set_security_service(mock_service)
        
        @require_permission(Permission.VIEW_DASHBOARD)
        def protected_function():
            return "Success"
        
        result = protected_function()
        assert result == "Success"
        mock_service.has_permission.assert_called_once_with(Permission.VIEW_DASHBOARD)
        
        # Cleanup
        set_security_service(None)
    
    def test_require_permission_denies_without_permission(self):
        """Verify that function is not executed when permission is missing."""
        mock_service = Mock(spec=SecurityService)
        mock_service.has_permission.return_value = False
        set_security_service(mock_service)
        
        @require_permission(Permission.DELETE_PRODUCT)
        def protected_function():
            return "Success"
        
        result = protected_function()
        assert result is None  # Function should return None when access denied
        
        # Cleanup
        set_security_service(None)


class TestRateLimiter:
    """Tests for RateLimiter service."""
    
    def setup_method(self):
        """Setup test database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, clear_mappers
        from database.models import Base
        
        # Create in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.rate_limiter = RateLimiter(self.SessionLocal)
    
    def teardown_method(self):
        """Cleanup after test."""
        self.engine.dispose()
    
    def test_allows_valid_attempts(self):
        """Verify that valid login attempts are allowed."""
        username = "test_user"
        
        # First attempt should be allowed
        allowed = self.rate_limiter.check_and_record_attempt(username, success=True)
        assert allowed is True
    
    def test_blocks_after_max_attempts(self):
        """Verify that user is blocked after maximum failed attempts."""
        username = "attacker"
        
        # Make 3 failed attempts
        for i in range(3):
            self.rate_limiter.check_and_record_attempt(username, success=False)
        
        # User should now be blocked
        is_blocked = self.rate_limiter.is_blocked(username)
        assert is_blocked is True
    
    def test_successful_login_resets_block(self):
        """Verify that successful login clears previous blocks."""
        username = "test_user"
        
        # Make failed attempts
        for i in range(2):
            self.rate_limiter.check_and_record_attempt(username, success=False)
        
        # Successful login
        self.rate_limiter.check_and_record_attempt(username, success=True)
        
        # Should not be blocked
        is_blocked = self.rate_limiter.is_blocked(username)
        assert is_blocked is False
    
    def test_cleanup_old_attempts(self):
        """Verify that old login attempts are cleaned up."""
        session = self.SessionLocal()
        
        # Create old attempt (25 hours ago)
        old_attempt = LoginAttempt(
            username="old_user",
            success=False,
            timestamp=datetime.now() - timedelta(hours=25)
        )
        session.add(old_attempt)
        session.commit()
        session.close()
        
        # Run cleanup
        self.rate_limiter.cleanup_old_attempts()
        
        # Verify old attempt was deleted
        session = self.SessionLocal()
        count = session.query(LoginAttempt).filter(LoginAttempt.username == "old_user").count()
        assert count == 0
        session.close()


class TestAuditLogger:
    """Tests for AuditLogger service."""
    
    def setup_method(self):
        """Setup test database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        # Create in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.audit_logger = AuditLogger(self.SessionLocal)
    
    def teardown_method(self):
        """Cleanup after test."""
        self.engine.dispose()
    
    def test_log_records_action(self):
        """Verify that audit logger recordsactions correctly."""
        self.audit_logger.log(
            username="admin",
            action="DELETE",
            entity_type="Product",
            entity_id=123,
            description="Deleted test product"
        )
        
        # Verify entry was created
        session = self.SessionLocal()
        entries = session.query(AuditLog).filter(AuditLog.username == "admin").all()
        assert len(entries) == 1
        assert entries[0].action == "DELETE"
        assert entries[0].entity_type == "Product"
        assert entries[0].entity_id == 123
        session.close()
    
    def test_log_login_success(self):
        """Verify successful login is logged."""
        self.audit_logger.log_login(username="user1", success=True, user_id=1)
        
        session = self.SessionLocal()
        entry = session.query(AuditLog).filter(AuditLog.username == "user1").first()
        assert entry is not None
        assert entry.action == "LOGIN"
        assert entry.success is True
        assert entry.user_id == 1
        session.close()
    
    def test_log_login_failure(self):
        """Verify failed login is logged with error message."""
        self.audit_logger.log_login(
            username="hacker",
            success=False,
            error_message="Invalid credentials"
        )
        
        session = self.SessionLocal()
        entry = session.query(AuditLog).filter(AuditLog.username == "hacker").first()
        assert entry is not None
        assert entry.action == "LOGIN"
        assert entry.success is False
        assert entry.error_message == "Invalid credentials"
        session.close()
    
    def test_log_logout(self):
        """Verify logout is logged."""
        self.audit_logger.log_logout(username="user1", user_id=1)
        
        session = self.SessionLocal()
        entry = session.query(AuditLog).filter(AuditLog.action == "LOGOUT").first()
        assert entry is not None
        assert entry.username == "user1"
        assert entry.user_id == 1
        session.close()
    
    def test_log_export(self):
        """Verify data export is logged."""
        self.audit_logger.log_export(
            username="admin",
            description="Exported all products to CSV"
        )
        
        session = self.SessionLocal()
        entry = session.query(AuditLog).filter(AuditLog.action == "EXPORT").first()
        assert entry is not None
        assert entry.description == "Exported all products to CSV"
        session.close()
    
    def test_audit_logger_handles_errors(self):
        """Verify that audit logger handles database errors gracefully."""
        def broken_session_factory():
            raise Exception("Database error")
        
        broken_logger = AuditLogger(broken_session_factory)
        
        try:
            broken_logger.log(username="test", action="TEST")
        except Exception:
            pytest.fail("AuditLogger.log no debería propagar excepciones de BD")
        assert broken_logger is not None  # logger sigue válido tras manejo de error
