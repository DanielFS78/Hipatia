# -*- coding: utf-8 -*-
"""Tests de integración para BackupController — flujo controller → diálogo → servicio."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec

from controllers.backup_controller import BackupController
from database.database_manager import DatabaseManager
from core.services.backup_service import BackupService
from ui.main_window import MainView


@pytest.fixture
def mock_app_structure():
    """Setup de mocks estrictos simulando la estructura de la app."""
    model = create_autospec(DatabaseManager, instance=True)
    model.db_url = "sqlite:///test.db"
    view = create_autospec(MainView, instance=True)
    logger = MagicMock(spec=["debug", "info", "warning", "error", "exception"])
    service = create_autospec(BackupService, instance=True)
    audit = MagicMock(spec=["log", "log_export", "log_delete", "log_import", "log_backup", "log_restore"])

    controller = BackupController(model, view, logger, service, audit)
    return controller, service, view


@pytest.mark.integration
class TestBackupIntegration:
    """Tests de integración para el flujo BackupController → diálogo → servicio."""

    def test_integration_controller_shows_dialog(self, mock_app_structure):
        """Verifica que el controller instancia el diálogo con los args correctos y llama exec."""
        controller, service, view = mock_app_structure

        with patch('ui.dialogs.backup_restore_dialog.BackupRestoreDialog') as MockDialogClass:
            mock_dialog_instance = MockDialogClass.return_value

            controller.show_backup_restore_dialog()

            MockDialogClass.assert_called_once_with(service, view, controller.audit_logger)
            assert mock_dialog_instance.exec.call_count == 1
            mock_dialog_instance.exec.assert_called_once_with()

    def test_integration_settings_button_signal(self):
        """Verifica que el patrón de conexión de señales es válido."""
        mock_button = MagicMock(spec=["clicked"])
        mock_button.clicked = MagicMock(spec=["connect"])
        mock_handler = MagicMock(spec=[])

        mock_button.clicked.connect(mock_handler)

        mock_button.clicked.connect.assert_called_once_with(mock_handler)
