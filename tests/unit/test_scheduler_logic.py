# -*- coding: utf-8 -*-
"""Tests unitarios para lógica de scheduler (StartupController): mantenimiento a las 02:00 e init timer."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QTime
from controllers.startup_controller import StartupController

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_app_controller():
    app = MagicMock(spec=["maintenance_service", "model", "view", "schedule_manager"])
    app.maintenance_service = MagicMock(spec=["run_background_maintenance"])
    app.model = MagicMock(spec=["db"])
    app.model.db = MagicMock(spec=["config_repo"])
    app.model.db.config_repo = MagicMock(spec=["get_setting"])
    app.model.db.config_repo.get_setting.return_value = "02:00"
    app.view = MagicMock(spec=[])
    app.schedule_manager = MagicMock(spec=[])
    return app

class TestSchedulerLogic:

    def test_check_scheduled_tasks_triggers_at_02_00(self, mock_app_controller):
        """Verifica que el mantenimiento se dispara a las 02:00."""
        # Setup controller
        startup = StartupController(mock_app_controller)
        
        # Patch QTime to simulate 02:00
        with patch('PyQt6.QtCore.QTime') as MockQTime:
            # Mock Scheduled Time (02:00)
            mock_scheduled = MagicMock(spec=["hour", "minute", "toString", "isValid"])
            mock_scheduled.hour.return_value = 2
            mock_scheduled.minute.return_value = 0
            mock_scheduled.toString.return_value = "02:00"
            mock_scheduled.isValid.return_value = True
            
            # Mock Current Time (02:00)
            mock_current = MagicMock(spec=["hour", "minute"])
            mock_current.hour.return_value = 2
            mock_current.minute.return_value = 0
            
            # Configure Class Mock
            MockQTime.fromString.return_value = mock_scheduled
            MockQTime.currentTime.return_value = mock_current
            
            # Execute
            startup._check_scheduled_tasks()
            
            assert mock_app_controller.maintenance_service.run_background_maintenance.call_count == 1
            mock_app_controller.maintenance_service.run_background_maintenance.assert_called_once_with()

    def test_check_scheduled_tasks_ignores_other_times(self, mock_app_controller):
        """Verifica que el mantenimiento NO se dispara a otras horas (ej. 02:01)."""
        startup = StartupController(mock_app_controller)
        
        with patch('PyQt6.QtCore.QTime') as MockQTime:
            # Mock Scheduled Time (02:00)
            mock_scheduled = MagicMock(spec=["hour", "minute", "toString", "isValid"])
            mock_scheduled.hour.return_value = 2
            mock_scheduled.minute.return_value = 0
            mock_scheduled.toString.return_value = "02:00"
            mock_scheduled.isValid.return_value = True
            
            # Mock Current Time (02:01)
            mock_current = MagicMock(spec=["hour", "minute"])
            mock_current.hour.return_value = 2
            mock_current.minute.return_value = 1
            
            MockQTime.fromString.return_value = mock_scheduled
            MockQTime.currentTime.return_value = mock_current
            
            # Execute
            startup._check_scheduled_tasks()
            
            assert mock_app_controller.maintenance_service.run_background_maintenance.call_count == 0
            mock_app_controller.maintenance_service.run_background_maintenance.assert_not_called()

    def test_init_scheduler_starts_timer(self, mock_app_controller):
        """Verifica que el scheduler inicializa y arranca el timer."""
        startup = StartupController(mock_app_controller)
        
        with patch('PyQt6.QtCore.QTimer') as MockQTimer:
            mock_timer_instance = MockQTimer.return_value
            
            startup._init_scheduler()
            
            assert MockQTimer.call_count >= 1
            MockQTimer.assert_called_with(startup.app)
            assert mock_timer_instance.timeout.connect.call_count == 1
            mock_timer_instance.timeout.connect.assert_called_with(startup._check_scheduled_tasks)
            assert mock_timer_instance.start.call_count == 1
            mock_timer_instance.start.assert_called_with(60000)
