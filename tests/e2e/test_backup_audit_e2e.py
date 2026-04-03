import pytest
from unittest.mock import ANY, MagicMock, patch
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from datetime import datetime

from core.dtos import BackupInfoDTO

@pytest.mark.e2e
# @pytest.mark.skip("Verificar manualmente en entorno con display o en CI con Xvfb.")
def test_e2e_backup_restore_flow(qapp, qtbot):

    """
    E2E Test: Simulates the flow of opening Backup Dialog, selecting a backup, 
    and verifying Audit Log call on restore.
    Requiere qapp (offscreen
para evitar crash en entornos sin display.
    """
    # 1. Setup Dependencies
    mock_service = MagicMock(spec=["list_available_backups", "restore_backup"])
    mock_service.list_available_backups.return_value = [
        BackupInfoDTO(
            name="backup_test.zip",
            path="/tmp/backup_test.zip",
            date=datetime(2023, 1, 1, 0, 0, 0),
            size_bytes=0,
            size_mb=10.5,
            has_checksum=True,
        )
    ]
    mock_service.restore_backup.return_value = (True, "/tmp/staging")
    mock_audit = MagicMock(spec=["log"])
    # 2. Initialize Dialog
    from ui.dialogs.backup_restore_dialog import BackupRestoreDialog
    dialog = BackupRestoreDialog(mock_service, audit_logger=mock_audit)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.wait(1)
    # 3. Interact: Select Backup
    assert dialog.backups_table.rowCount() == 1
    dialog.backups_table.selectRow(0)
    dialog._on_selection_changed()
    # Verify button enabled
    assert dialog.restore_btn.isEnabled()
    # 4. Interact: Click Restore & Handle Confirmation
    # We patch QMessageBox to auto-accept warnings/info
    # Also patch QProgressDialog
    with patch('PyQt6.QtWidgets.QProgressDialog') as MockProgress:
        with patch.object(QMessageBox, 'warning', return_value=QMessageBox.StandardButton.Ok) as mock_warn, \
             patch.object(QMessageBox, 'information') as mock_info:
            
            qtbot.mouseClick(dialog.restore_btn, Qt.MouseButton.LeftButton)
            # 5. Verify Logic
            # Warning shown?
            assert mock_warn.call_count == 1
            mock_warn.assert_called_once_with(ANY, ANY, ANY, ANY, ANY)
            # Service called?
            assert mock_service.restore_backup.call_count >= 1
            mock_service.restore_backup.assert_called_with('backup_test.zip')
            # Success message shown?
            assert mock_info.call_count == 1
            mock_info.assert_called_once_with(ANY, ANY, ANY)
# Audit Logged?
            args = mock_audit.log.call_args
            assert args is not None
            call_kwargs = args[1] if args[1] else args[0] # Handle args vs kwargs
            # Look for kwargs
            assert mock_audit.log.call_count == 1
            # Check specific args if possible, but at least verify it was called
             
    dialog.close()

@pytest.mark.e2e
# @pytest.mark.skip("Verificar manualmente en entorno con display o en CI con Xvfb.")
def test_e2e_backup_restore_failure_audit(qapp, qtbot):

    """
    E2E Test: Simulates restore failure and verifies logging.
    Requiere qapp (offscreen
para evitar crash en entornos sin display.
    """
    mock_service = MagicMock(spec=["list_available_backups", "restore_backup"])
    mock_service.list_available_backups.return_value = [
        BackupInfoDTO(
            name="fail.zip",
            path="/tmp/fail.zip",
            date=datetime(2023, 1, 1, 0, 0, 0),
            size_bytes=0,
            size_mb=1.0,
            has_checksum=True,
        )
    ]
    mock_service.restore_backup.return_value = (False, "")
    mock_audit = MagicMock(spec=["log"])
    from ui.dialogs.backup_restore_dialog import BackupRestoreDialog
    dialog = BackupRestoreDialog(mock_service, audit_logger=mock_audit)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.wait(1)
    dialog.backups_table.selectRow(0)
    dialog._on_selection_changed()
    # Patch QProgressDialog to avoid blocking
    with patch('PyQt6.QtWidgets.QProgressDialog') as MockProgress:
        mock_progress_instance = MockProgress.return_value
        
        with patch.object(QMessageBox, 'warning', return_value=QMessageBox.StandardButton.Ok), \
             patch.object(QMessageBox, 'critical') as mock_crit:
             
             qtbot.mouseClick(dialog.restore_btn, Qt.MouseButton.LeftButton)
             assert mock_crit.call_count == 1
             mock_crit.assert_called_once_with(ANY, ANY, ANY)
             # Verify Audit Failure Log
             assert mock_audit.log.call_count == 1
         # We could verify success=False argument if we dig into call_args
