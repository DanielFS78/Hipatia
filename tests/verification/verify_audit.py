
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from controllers.backup_controller import BackupController

def test_audit_integration():
    """Verifica que BackupController registra eventos de auditoría."""
    print("Testing Audit Integration...")
    
    mock_model = MagicMock()
    mock_view = MagicMock()
    mock_logger = MagicMock()
    mock_backup_service = MagicMock()
    mock_audit_logger = MagicMock()
    
    controller = BackupController(mock_model, mock_view, mock_logger, mock_backup_service, mock_audit_logger)
    
    # 1. Verify Auto Backup Logging
    # create_automatic_backup success
    mock_backup_service.list_available_backups.return_value = [] # Mock calls inside if any
    # We need to mock _create_backup_directory_structure and os.path.exists and shutil.copy2
    # This is complex to mock fully for unit test validation of LOGGING only.
    # Let's verify via 'create_automatic_backup' logic if simple helpers are mocked.
    
    with patch.object(controller, '_create_backup_directory_structure', return_value=('/tmp/db', '/tmp/log')):
        with patch.object(controller, '_get_db_path', return_value='/tmp/db.sqlite'):
            with patch('os.path.exists', return_value=True):
                with patch('shutil.copy2'):
                     with patch.object(controller, '_backup_and_clean_log', return_value=True):
                         controller.create_automatic_backup()
                         
                         # Check audit log
                         args = mock_audit_logger.log.call_args
                         if args and args[1]['action'] == 'BACKUP_AUTO' and args[1]['success'] == True:
                             print("✅ Automatic Backup Success Logged")
                         else:
                             print(f"❌ Automatic Backup Log Missing or Incorrect: {mock_audit_logger.log.call_args}")

    # 2. Verify Export Logging
    mock_audit_logger.reset_mock()
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=('/tmp/backup.zip', 'zip')):
         with patch('zipfile.ZipFile'):
             with patch('os.path.exists', return_value=True):
                # Mock resource_path
                with patch('controllers.backup_controller.resource_path', return_value='/tmp/db.sqlite'):
                    controller.on_export_databases()
                    
                    if mock_audit_logger.log_export.called:
                        print("✅ Export Action Logged")
                    else:
                        print("❌ Export Action NOT Logged")

if __name__ == "__main__":
    test_audit_integration()
