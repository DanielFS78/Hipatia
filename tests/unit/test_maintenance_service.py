"""Tests para MaintenanceService."""
import pytest
from unittest.mock import ANY, MagicMock, patch
from core.services.maintenance_service import MaintenanceService
from core.services.rate_limiter import RateLimiter
from core.services.audit_logger import AuditLogger

pytestmark = pytest.mark.unit


class TestMaintenanceService:
    @pytest.fixture
    def mock_rate_limiter(self):
        return MagicMock(spec=RateLimiter)
    
    @pytest.fixture
    def mock_audit_logger(self):
        return MagicMock(spec=AuditLogger)
        
    @pytest.fixture
    def maintenance_service(self, mock_rate_limiter, mock_audit_logger):
        return MaintenanceService(mock_rate_limiter, mock_audit_logger)
        
    def test_perform_maintenance_calls_cleanup(self, maintenance_service, mock_rate_limiter, mock_audit_logger):
        """Test that perform_maintenance calls cleanup methods on services."""
        maintenance_service.perform_maintenance()
        
        assert mock_rate_limiter.cleanup_old_attempts.call_count == 1
        mock_rate_limiter.cleanup_old_attempts.assert_called_once_with()
        mock_audit_logger.cleanup_old_logs.assert_called_once_with(retention_days=365)
        
    def test_run_background_maintenance(self, maintenance_service):
        """Test that run_background_maintenance starts a thread."""
        with patch('PyQt6.QtCore.QThreadPool.globalInstance') as mock_pool_static:
            mock_pool_instance = MagicMock(spec=["start"])
            mock_pool_static.return_value = mock_pool_instance
            
            # Re-init to get the mocked pool
            maintenance_service.thread_pool = mock_pool_instance
            
            maintenance_service.run_background_maintenance()
            
            assert mock_pool_instance.start.call_count == 1
            # QThreadPool.start recibe un QRunnable (MaintenanceWorker)
            mock_pool_instance.start.assert_called_once_with(ANY)
            args = mock_pool_instance.start.call_args[0]
            assert args[0].service == maintenance_service
