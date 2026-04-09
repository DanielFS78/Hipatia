
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QTime

# Add project root to path
sys.path.append(os.getcwd())

from controllers.startup_controller import StartupController

def test_scheduler_triggers_maintenance():
    """Verifica que el scheduler dispara el mantenimiento a la hora correcta."""
    print("Testing Scheduler Trigger...")
    
    # Mock AppController and dependencies
    mock_app_controller = MagicMock()
    mock_app_controller.schedule_manager = MagicMock()
    mock_app_controller.model = MagicMock()
    mock_app_controller.model.db = MagicMock()
    mock_app_controller.model.db.config_repo = MagicMock()
    mock_app_controller.model.db.config_repo.get_setting.return_value = "02:00"
    mock_app_controller.view = MagicMock()
    
    # Mock MaintenanceService
    mock_maintenance_service = MagicMock()
    mock_app_controller.maintenance_service = mock_maintenance_service
    
    # Instantiate StartupController
    startup_controller = StartupController(mock_app_controller)
    
    # 1. Test Matching Time (02:00)
    # We need to patch QTime inside startup_controller module namespace or where it's imported
    # Since it imports 'from PyQt6.QtCore import QTime' inside the method, we patch 'PyQt6.QtCore.QTime'
    
    # 1. Test Matching Time (02:00)
    
    with patch('PyQt6.QtCore.QTime') as mock_qtime:
        # Setup what QTime(2, 0) returns (the scheduled time)
        mock_scheduled_time = MagicMock()
        mock_scheduled_time.hour.return_value = 2
        mock_scheduled_time.minute.return_value = 0
        mock_scheduled_time.toString.return_value = "02:00"
        
        # Setup what QTime.currentTime() returns (the current time)
        mock_current_time = MagicMock()
        mock_current_time.hour.return_value = 2
        mock_current_time.minute.return_value = 0
        
        # Configure the class mock
        mock_qtime.return_value = mock_scheduled_time  # Constructor for SCHEDULED_BACKUP_TIME
        mock_qtime.currentTime.return_value = mock_current_time
        
        # Ejecutar chequeo
        startup_controller._check_scheduled_tasks()
        
        # Verificar llamada
        if mock_maintenance_service.run_background_maintenance.called:
            print("✅ Scheduler triggered maintenance at 02:00")
        else:
            print("❌ Scheduler FAILED to trigger maintenance at 02:00")

    # 2. Test Non-Matching Time (02:01)
    mock_maintenance_service.reset_mock()
    with patch('PyQt6.QtCore.QTime') as mock_qtime:
        # Scheduled time is still 02:00
        mock_scheduled_time = MagicMock()
        mock_scheduled_time.hour.return_value = 2
        mock_scheduled_time.minute.return_value = 0
        
        # Current time is 02:01
        mock_current_time = MagicMock()
        mock_current_time.hour.return_value = 2
        mock_current_time.minute.return_value = 1
        
        mock_qtime.return_value = mock_scheduled_time
        mock_qtime.currentTime.return_value = mock_current_time
        
        startup_controller._check_scheduled_tasks()
        
        if not mock_maintenance_service.run_background_maintenance.called:
            print("✅ Scheduler correctly IGNORED time 02:01")
        else:
            print("❌ Scheduler incorrectly triggered at 02:01")

if __name__ == "__main__":
    test_scheduler_triggers_maintenance()
